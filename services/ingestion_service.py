from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

from guardrails.heuristics import run_guardrail_checks, summarize_guardrail_issues
from vpb_ai_logic import build_prompt_for_ingestion
from vpb_diff import validate_add_only_diff

try:  # Optional Import, abhängig von Minimal-Setup
    from ollama_client import OllamaClient, OllamaOptions  # type: ignore
except Exception:  # pragma: no cover
    OllamaClient = None  # type: ignore
    OllamaOptions = None  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    from controller.app_controller import TaskContext


def _ctx_check(context: "TaskContext | None") -> None:
    if context is None:
        return
    check = getattr(context, "check_cancelled", None)
    if callable(check):
        check()


def _ctx_progress(
    context: "TaskContext | None",
    *,
    fraction: Optional[float] = None,
    message: Optional[str] = None,
    **fields: Any,
) -> None:
    if context is None:
        return
    publish = getattr(context, "publish_progress", None)
    if callable(publish):
        try:
            publish(fraction=fraction, message=message, **fields)
        except Exception:
            pass


class IngestionService:
    """Bereitet Quellen auf, erzeugt einen Ingestion-Prompt und validiert das LLM-Ergebnis."""

    MAX_FILE_BYTES = 256 * 1024
    MAX_TEXT_CHARS = 6000
    MAX_INLINE_CHARS = 6000
    MAX_CSV_ROWS = 25
    MAX_CSV_COLS = 20
    MAX_DIAGRAM_SUMMARY_CHARS = 8000
    LOG_DIR = "logs"

    def run(self, payload: Dict[str, Any], context: "TaskContext | None" = None) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("payload muss ein Dict sein")
        request = payload.get("request") or {}
        sources: List[str] = list(request.get("sources") or [])
        inline_text: str = str(request.get("inline_text") or "")
        prompt_context: str = str(request.get("prompt_context") or "")
        options: Dict[str, Any] = request.get("options") or {}

        if not sources and not inline_text.strip():
            raise ValueError("Keine Quellen oder Freitext übergeben")

        element_types: List[str] = list(payload.get("element_types") or [])
        connection_types: List[str] = list(payload.get("connection_types") or [])
        current_diagram: Dict[str, Any] = payload.get("current_diagram") or {}
        settings: Dict[str, Any] = payload.get("settings") or {}

        endpoint = settings.get("endpoint") or payload.get("endpoint")
        model = settings.get("model") or payload.get("model")
        temperature = settings.get("temperature", payload.get("temperature", 0.2))
        num_predict = settings.get("num_predict", payload.get("num_predict", 600))

        if not endpoint or not model:
            raise RuntimeError("Ollama Endpoint/Modell nicht konfiguriert")
        if OllamaClient is None or OllamaOptions is None:
            raise RuntimeError("OllamaClient nicht verfügbar")

        _ctx_progress(context, fraction=0.03, message="Quellen werden gelesen")
        source_text, source_preview, preparation_warnings = self._prepare_sources(sources, inline_text, context=context)

        _ctx_progress(context, fraction=0.12, message="Diagramm wird zusammengefasst")
        diagram_summary = self._build_diagram_summary(current_diagram)

        include_prompt = bool(options.get("include_prompt"))
        include_raw = bool(options.get("include_raw"))

        _ctx_progress(context, fraction=0.2, message="Prompt wird erstellt")
        prompt, meta = build_prompt_for_ingestion(
            source_text,
            element_types,
            connection_types,
            prompt_context=prompt_context,
            current_diagram_summary=diagram_summary,
            example_tags=options.get("example_tags") or None,
            return_meta=True,
        )

        _ctx_check(context)

        existing_element_ids = [
            str(e.get("element_id"))
            for e in current_diagram.get("elements", [])
            if isinstance(e, dict) and e.get("element_id")
        ]
        existing_connection_ids = [
            str(c.get("connection_id"))
            for c in current_diagram.get("connections", [])
            if isinstance(c, dict) and c.get("connection_id")
        ]
        existing_ids = existing_element_ids + existing_connection_ids

        client = OllamaClient(endpoint=endpoint, model=model)
        ollama_options = OllamaOptions(temperature=temperature, num_predict=num_predict)

        retries = int(payload.get("retries") or options.get("retries") or 1)
        tolerance = str(payload.get("tolerance") or options.get("tolerance") or "lenient")
        _ctx_progress(context, fraction=0.32, message="LLM wird angefragt")
        result = client.generate_vpb_validated(
            prompt,
            mode="ingestion_diff",
            existing_ids=existing_ids,
            allow_element_types=element_types,
            allow_connection_types=connection_types,
            options=ollama_options,
            retries=max(0, retries - 1),
            tolerance=tolerance,
        )

        validation = result.get("validation") or {}
        if not isinstance(validation, dict):
            raise RuntimeError("Validierungsergebnis fehlt")
        parsed_diff = validation.get("parsed")
        fatal = bool(validation.get("fatal"))
        issues = validation.get("issues") or []
        if not isinstance(issues, list):
            issues = []
        repairs = validation.get("repairs") or []
        if not isinstance(repairs, list):
            repairs = []
        if not isinstance(parsed_diff, dict):
            raise RuntimeError("LLM-Antwort enthielt kein gültiges Diff")
        if fatal:
            raise RuntimeError("LLM-Antwort nicht verwertbar (fataler Validierungsfehler)")

        _ctx_progress(context, fraction=0.74, message="Diff wird validiert")
        ok, err = validate_add_only_diff(parsed_diff, existing_element_ids, element_types, connection_types)
        if not ok:
            raise RuntimeError(f"Add-Only-Diff ungültig: {err}")

        guardrail_issues = run_guardrail_checks(current_diagram, diff=parsed_diff)
        guardrail_summary = summarize_guardrail_issues(guardrail_issues)

        raw_text = result.get("raw", "")
        if not isinstance(raw_text, str):
            raw_text = str(raw_text)

        warnings: List[str] = list(preparation_warnings)
        if issues:
            for it in issues:
                try:
                    code = it.get("code", "issue")
                    severity = it.get("severity", "info")
                    msg = it.get("message", "")
                    warnings.append(f"{severity.upper()} {code}: {msg}")
                except Exception:
                    continue
        if repairs:
            for repair in repairs:
                try:
                    warnings.append(f"REPAIR: {repair}")
                except Exception:
                    continue
        if guardrail_issues:
            for issue in guardrail_issues:
                try:
                    warnings.append(f"GUARD {issue.code}: {issue.message}")
                except Exception:
                    continue

        _ctx_progress(context, fraction=0.92, message="Protokoll wird geschrieben")
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sources": source_preview,
            "prompt_meta": asdict(meta),
            "warnings": warnings,
            "issues": issues,
            "repairs": repairs,
            "guardrail_issues": [issue.to_dict() for issue in guardrail_issues],
            "guardrail_summary": guardrail_summary,
            "attempts": result.get("attempts"),
            "diff_summary": {
                "elements": len(parsed_diff.get("elements", []) if isinstance(parsed_diff, dict) else []),
                "connections": len(parsed_diff.get("connections", []) if isinstance(parsed_diff, dict) else []),
            },
        }
        self._write_log(log_entry)

        _ctx_progress(context, fraction=1.0, message="Ingestion abgeschlossen")
        response: Dict[str, Any] = {
            "diff": parsed_diff,
            "warnings": warnings,
            "issues": issues,
            "source_preview": source_preview,
            "prompt_meta": asdict(meta),
            "attempts": result.get("attempts"),
            "sources_prompt": source_text,
            "guardrail_issues": [issue.to_dict() for issue in guardrail_issues],
            "guardrail_summary": guardrail_summary,
        }
        if include_prompt:
            response["prompt"] = prompt
        if include_raw:
            response["raw_output"] = raw_text
        return response

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _prepare_sources(
        self,
        paths: Iterable[str],
        inline_text: str,
        *,
        context: "TaskContext | None" = None,
    ) -> Tuple[str, List[Dict[str, Any]], List[str]]:
        sections: List[str] = []
        preview: List[Dict[str, Any]] = []
        warnings: List[str] = []

        for idx, path in enumerate(paths, 1):
            _ctx_check(context)
            if not path:
                continue
            if not os.path.exists(path):
                warnings.append(f"Datei nicht gefunden: {path}")
                continue
            try:
                size = os.path.getsize(path)
            except Exception:
                size = None
            if size is not None and size > self.MAX_FILE_BYTES:
                warnings.append(f"Datei zu groß und wird übersprungen ({path})")
                continue

            ext = os.path.splitext(path)[1].lower()
            try:
                if ext in {".csv"}:
                    content, meta = self._read_csv(path)
                else:
                    content, meta = self._read_text(path)
            except Exception as exc:
                warnings.append(f"Fehler beim Lesen von {path}: {exc}")
                continue
            meta.update({"path": path, "index": idx})
            sections.append(self._format_source_section(meta, content))
            preview.append(meta)

        inline_clean = inline_text.strip()
        if inline_clean:
            truncated = self._truncate(inline_clean, self.MAX_INLINE_CHARS)
            sections.append(self._format_inline_section(truncated))
            preview.append(
                {
                    "type": "inline_text",
                    "characters": len(inline_clean),
                    "truncated": len(truncated) < len(inline_clean),
                }
            )

        if not sections:
            sections.append("(Keine gültigen Quellen verfügbar)")

        return "\n\n".join(sections), preview, warnings

    def _read_text(self, path: str) -> Tuple[str, Dict[str, Any]]:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = f.read()
        truncated = self._truncate(data, self.MAX_TEXT_CHARS)
        meta = {
            "type": "text",
            "characters": len(data),
            "truncated": len(truncated) < len(data),
        }
        return truncated, meta

    def _read_csv(self, path: str) -> Tuple[str, Dict[str, Any]]:
        rows: List[List[str]] = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for r_idx, row in enumerate(reader):
                if r_idx >= self.MAX_CSV_ROWS:
                    break
                rows.append(row[: self.MAX_CSV_COLS])
        # Konvertiere in Markdown-Tabelle für bessere Lesbarkeit im Prompt
        if not rows:
            content = "(Leere CSV-Datei)"
        else:
            header = rows[0]
            body = rows[1:]
            header_line = " | ".join(header)
            separator = " | ".join(["---"] * len(header))
            body_lines = [" | ".join(r) for r in body]
            content = "\n".join([header_line, separator, *body_lines])
        meta = {
            "type": "csv",
            "rows": len(rows),
            "columns": max((len(r) for r in rows), default=0),
            "truncated": False,
        }
        return content, meta

    @staticmethod
    def _format_source_section(meta: Dict[str, Any], content: str) -> str:
        label = meta.get("path") or meta.get("name") or "Quelle"
        info_parts = []
        if meta.get("type"):
            info_parts.append(str(meta.get("type")))
        if meta.get("rows"):
            info_parts.append(f"{meta['rows']} Zeilen")
        if meta.get("columns"):
            info_parts.append(f"{meta['columns']} Spalten")
        if meta.get("characters"):
            info_parts.append(f"{meta['characters']} Zeichen")
        info = ", ".join(info_parts)
        truncated = meta.get("truncated")
        if truncated:
            info = (info + "; gekürzt") if info else "(gekürzt)"
        return f"Quelle: {label} ({info})\n{content.strip()}"

    @staticmethod
    def _format_inline_section(content: str) -> str:
        return "Inline-Text:\n" + content.strip()

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        if limit <= 0 or len(text) <= limit:
            return text
        return text[:limit] + "\n…"

    def _build_diagram_summary(self, diagram: Dict[str, Any]) -> str:
        if not isinstance(diagram, dict):
            return "(kein Diagramm übergeben)"
        meta = diagram.get("metadata", {}) or {}
        elements = diagram.get("elements", []) or []
        connections = diagram.get("connections", []) or []
        lines = [
            f"Name: {meta.get('name', '-')}",
            f"Beschreibung: {self._truncate(str(meta.get('description', '')), 200)}",
            f"Elemente gesamt: {len(elements)}",
            f"Verbindungen gesamt: {len(connections)}",
        ]
        preview_limit = 12
        for idx, el in enumerate(elements[:preview_limit], 1):
            eid = el.get("element_id")
            etype = el.get("element_type")
            name = el.get("name")
            lines.append(f"Element {idx}: {eid} ({etype}) – {name}")
        if len(elements) > preview_limit:
            lines.append(f"… (+{len(elements) - preview_limit} weitere Elemente)")
        return "\n".join(lines)[: self.MAX_DIAGRAM_SUMMARY_CHARS]

    def _write_log(self, entry: Dict[str, Any]) -> None:
        try:
            os.makedirs(self.LOG_DIR, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(self.LOG_DIR, f"ingestion_{ts}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
        except Exception:
            # Logging ist optional – Fehler hier werden still ignoriert
            pass
