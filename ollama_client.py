#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfache Ollama-HTTP-Client-Wrapper ohne externe Abhängigkeiten (urllib).
Unterstützt: health (Tags abrufen), generate (Prompt → Text), chat (Nachrichtenliste).
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Iterator, Callable, Tuple
import threading
import queue
import re

try:
    import dirtyjson  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    dirtyjson = None  # type: ignore

# VPB spezifische Validierung (optional import, weich fall-back)
try:
    from vpb_ai_logic import validate_model_output
except Exception:  # pragma: no cover - falls Modul im Minimalmodus nicht verfügbar
    validate_model_output = None  # type: ignore


@dataclass
class OllamaOptions:
    temperature: Optional[float] = None
    num_predict: Optional[int] = None  # max_tokens

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {}
        if self.temperature is not None:
            d["temperature"] = float(self.temperature)
        if self.num_predict is not None:
            d["num_predict"] = int(self.num_predict)
        return d


class OllamaClient:
    def __init__(self, endpoint: str = "http://localhost:11434", model: str = "llama3.2:latest", timeout: int = 60):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    # --- Low-level HTTP ---
    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8")
            # Ollama kann im Streaming-Fall Zeilen-JSON senden; hier verwenden wir stream=False
            return json.loads(body)

    def _post_json_stream(self, path: str, payload: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """POST mit stream=True und Ereignisse zeilenweise als Dict liefern."""
        url = f"{self.endpoint}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        resp = urllib.request.urlopen(req, timeout=self.timeout)
        # Achtung: Aufrufer muss den Generator vollständig konsumieren oder resp.close() sicherstellen
        try:
            for raw in resp:
                if not raw:
                    continue
                try:
                    line = raw.decode("utf-8").strip()
                except Exception:
                    continue
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    yield evt
                except Exception:
                    # falls mal kein vollständiges JSON
                    continue
        finally:
            try:
                resp.close()
            except Exception:
                pass

    def _get_json(self, path: str) -> Dict[str, Any]:
        url = f"{self.endpoint}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)

    # --- API ---
    def health(self) -> Dict[str, Any]:
        """Liefert Model-Tags; dient als Health-Check."""
        try:
            return self._get_json("/api/tags")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama Health-Check fehlgeschlagen: {e}")

    def generate(self, prompt: str, options: Optional[OllamaOptions] = None, stream: bool = False) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": bool(stream),
        }
        if options:
            payload["options"] = options.to_dict()
        try:
            if stream:
                # Nicht-blockierend: Aufrufer sollte generate_stream nutzen
                chunks = []
                for evt in self._post_json_stream("/api/generate", payload):
                    if "response" in evt:
                        chunks.append(str(evt.get("response", "")))
                return "".join(chunks)
            else:
                res = self._post_json("/api/generate", payload)
                # Erwartete Antwort: {"response": "...", "done": true, ...}
                return str(res.get("response", ""))
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama generate fehlgeschlagen: {e}")

    def chat(self, messages: List[Dict[str, str]], options: Optional[OllamaOptions] = None, stream: bool = False) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": bool(stream),
        }
        if options:
            payload["options"] = options.to_dict()
        try:
            if stream:
                chunks = []
                for evt in self._post_json_stream("/api/chat", payload):
                    # Chat-Streaming liefert meist {"message": {"content": "..."}, "done": false}
                    msg = evt.get("message", {}) or {}
                    if "content" in msg:
                        chunks.append(str(msg.get("content", "")))
                return "".join(chunks)
            else:
                res = self._post_json("/api/chat", payload)
                msg = res.get("message", {}) or {}
                return str(msg.get("content", ""))
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama chat fehlgeschlagen: {e}")

    # --- Streaming-Generatoren ---
    def generate_stream(self, prompt: str, options: Optional[OllamaOptions] = None) -> Iterator[str]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
        }
        if options:
            payload["options"] = options.to_dict()
        for evt in self._post_json_stream("/api/generate", payload):
            if "response" in evt:
                yield str(evt.get("response", ""))

    def chat_stream(self, messages: List[Dict[str, str]], options: Optional[OllamaOptions] = None) -> Iterator[str]:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        if options:
            payload["options"] = options.to_dict()
        for evt in self._post_json_stream("/api/chat", payload):
            msg = evt.get("message", {}) or {}
            if "content" in msg:
                yield str(msg.get("content", ""))

    # --- VPB Spezifischer Helfer ---
    def generate_vpb_validated(
        self,
        prompt: str,
        *,
        mode: str,
        existing_ids: Optional[List[str]] = None,
        allow_element_types: Optional[List[str]] = None,
        allow_connection_types: Optional[List[str]] = None,
        options: Optional[OllamaOptions] = None,
        retries: int = 1,
        tolerance: str = "strict",
    ) -> Dict[str, Any]:
        """Spezialisierte Erzeugung für VPB-Diagramm-Modi mit nachgelagerter Validierung.

        Ablauf:
        1. Modell-Text generieren (generate)
        2. Validierung via validate_model_output (Prompt-Core)
        3. Bei fatalem Fehler optional Retry mit verschärfter Instruktion

        Rückgabe: dict { 'raw': str, 'validation': {parsed, issues, fatal}, 'attempts': n }
        """
        if validate_model_output is None:
            raise RuntimeError("validate_model_output nicht verfügbar – Modul vpb_ai_logic fehlt")
        attempt = 0
        base_prompt = prompt
        last_validation: Optional[Dict[str, Any]] = None
        raw_text: str = ""
        while True:
            raw_text = self.generate(base_prompt, options=options, stream=False)
            last_validation = validate_model_output(
                raw_text,
                mode=mode,
                existing_ids=existing_ids or [],
                allow_element_types=allow_element_types or [],
                allow_connection_types=allow_connection_types or [],
                tolerance=tolerance,
            )
            if not last_validation.get("fatal"):
                return {"raw": raw_text, "validation": last_validation, "attempts": attempt + 1}
            if attempt >= retries:
                return {"raw": raw_text, "validation": last_validation, "attempts": attempt + 1}
            # Verschärfter Prompt für nächsten Versuch: fokussiere auf JSON-only + Fehlerliste
            issues_txt = "; ".join(f"{i['code']}" for i in last_validation.get("issues", [])[:5])
            base_prompt = (
                "ANTWORTE NUR mit einem einzelnen gültigen JSON-Objekt ohne Kommentare oder Erklärtexte. "
                "Behebe die Validierungsprobleme (" + issues_txt + "). Vorherige Anweisung bleibt maßgeblich.\n\n"
                + prompt
            )
            attempt += 1

    # --- JSON-Helfer ---
    @staticmethod
    def extract_json(text: str) -> Any:
        """Robuste JSON-Extraktion aus freiem Text. Unterstützt ```json ...```-Blöcke oder rohe JSON-Blöcke.
        Wirft ValueError, wenn keine gültige JSON-Struktur gefunden wird.
        """
        if not isinstance(text, str):
            raise ValueError("Text ist nicht vom Typ str")
        s = text.strip()
        # Codefence ```json ... ``` oder ``` ... ```
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", s, re.IGNORECASE)
        if fence:
            candidate = fence.group(1).strip()
            parsed, errors = OllamaClient._try_parse_with_fallbacks(candidate)
            if parsed is not None:
                return OllamaClient._sanitize_vpb_structure(parsed)
        # Ersten { bis letzten } nehmen (rudimentär)
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = s[start:end + 1]
            parsed, errors = OllamaClient._try_parse_with_fallbacks(candidate)
            if parsed is not None:
                return OllamaClient._sanitize_vpb_structure(parsed)
            message = errors[-1] if errors else "Unbekannter Fehler"
            raise ValueError(f"JSON konnte nicht geparst werden: {message}")
        raise ValueError("Kein JSON im Text gefunden")

    @staticmethod
    def _try_parse_with_fallbacks(candidate: str) -> Tuple[Any | None, List[str]]:
        parsers: List[Callable[[str], Any]] = [json.loads]
        # Trailing commas entfernen als schnelle Heuristik
        def _strip_trailing_commas(payload: str) -> Any:
            cleaned = re.sub(r",\s*([}\]])", r"\1", payload)
            return json.loads(cleaned)

        parsers.append(_strip_trailing_commas)

        if dirtyjson is not None:
            parsers.append(dirtyjson.loads)  # type: ignore[arg-type]

        errors: List[str] = []
        for parser in parsers:
            try:
                return parser(candidate), errors
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))
        return None, errors

    @staticmethod
    def _sanitize_vpb_structure(data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        def _sanitize_element(elem: Any) -> Any:
            if not isinstance(elem, dict):
                return elem
            defaults = {
                "description": "",
                "responsible_authority": "unbekannt",
                "legal_basis": "n.n.",
                "deadline_days": 0,
                "geo_reference": "",
            }
            for key, default in defaults.items():
                val = elem.get(key)
                if val is None:
                    elem[key] = default
            # numerische Normalisierung
            for coord in ("x", "y"):
                if coord in elem:
                    try:
                        elem[coord] = int(elem[coord])
                    except Exception:
                        elem[coord] = 0
            if "deadline_days" in elem:
                try:
                    elem["deadline_days"] = int(elem["deadline_days"])
                except Exception:
                    elem["deadline_days"] = 0
            return elem

        def _sanitize_connection(conn: Any) -> Any:
            if not isinstance(conn, dict):
                return conn
            if conn.get("description") is None:
                conn["description"] = ""
            return conn

        def _sanitize_elements_container(container: Any) -> Any:
            if isinstance(container, list):
                return [_sanitize_element(elem) for elem in container if elem is not None]
            if container is None:
                return []
            return container

        def _sanitize_connections_container(container: Any) -> Any:
            if isinstance(container, list):
                return [_sanitize_connection(conn) for conn in container if conn is not None]
            if container is None:
                return []
            return container

        if "metadata" in data and isinstance(data["metadata"], dict):
            metadata_defaults = {"name": "", "description": ""}
            for key, default in metadata_defaults.items():
                if data["metadata"].get(key) is None:
                    data["metadata"][key] = default

        if "elements" in data:
            data["elements"] = _sanitize_elements_container(data.get("elements"))

        if "connections" in data:
            data["connections"] = _sanitize_connections_container(data.get("connections"))

        patch = data.get("patch")
        if isinstance(patch, dict):
            if "elements" in patch:
                patch["elements"] = _sanitize_elements_container(patch.get("elements"))
            if "connections" in patch:
                patch["connections"] = _sanitize_connections_container(patch.get("connections"))

        return data

    def generate_json(self, prompt: str, options: Optional[OllamaOptions] = None, retries: int = 1,
                      validate: Optional[Callable[[Any], Tuple[bool, Optional[str]]]] = None) -> Any:
        """Erzeugt Text via generate() und extrahiert JSON. Optional Validierung per Callback.
        retries: bei Parse-/Validierungsfehlern wird mit verstärkter Instruktion neu versucht.
        validate: Callable, das (ok, fehlertext) zurückgibt.
        """
        attempt = 0
        last_err: Optional[str] = None
        base_prompt = prompt
        while True:
            txt = self.generate(base_prompt, options=options, stream=False)
            try:
                data = self.extract_json(txt)
            except Exception as e:
                last_err = str(e)
                data = None
            if data is not None and validate is not None:
                try:
                    ok, err = validate(data)
                except Exception as ve:
                    ok, err = False, f"Validator-Fehler: {ve}"
                if not ok:
                    last_err = err or "Ungültige JSON-Struktur"
                    data = None
            if data is not None:
                return data
            if attempt >= max(0, int(retries)):
                raise RuntimeError(f"generate_json fehlgeschlagen: {last_err or 'Unbekannter Fehler'}")
            # Prompt verschärfen
            base_prompt = (
                "Gib ausschließlich gültiges JSON ohne Kommentare oder Erklärungen zurück. "
                "Wenn du zuvor Text gemischt mit JSON geliefert hast, liefere jetzt nur das JSON-Objekt.\n\n"
                f"Ursprüngliche Anweisung:\n{prompt}\n\nVorheriger Fehler: {last_err}"
            )
            attempt += 1


class OllamaJob:
    """Einfache Threading-Hülle für Ollama-Aufrufe mit best-effort Cancel-Unterstützung.
    Für Streaming-Aufrufe wird der Generator im Thread konsumiert und Stücke in eine Queue gelegt.
    Für nicht-streamende Aufrufe wird das Gesamtergebnis in die Queue gelegt.
    """
    def __init__(self, target: Callable, *args, **kwargs):
        self._target = target
        self._args = args
        self._kwargs = kwargs
        self._q: "queue.Queue[Any]" = queue.Queue()
        self._cancel = threading.Event()
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        try:
            res = self._target(*self._args, **self._kwargs)
            # Streaming-Generator erkennen
            if hasattr(res, "__iter__") and not isinstance(res, (str, bytes, dict, list)):
                for chunk in res:
                    if self._cancel.is_set():
                        break
                    self._q.put(chunk)
            else:
                self._q.put(res)
        except Exception as e:
            self._q.put(e)
        finally:
            self._done.set()

    def start(self):
        self._thread.start()
        return self

    def cancel(self):
        self._cancel.set()

    def is_cancelled(self) -> bool:
        return self._cancel.is_set()

    def is_done(self) -> bool:
        return self._done.is_set()

    def get_nowait(self) -> Optional[Any]:
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def get(self, timeout: Optional[float] = None) -> Any:
        return self._q.get(timeout=timeout)

    def join(self, timeout: Optional[float] = None):
        self._thread.join(timeout=timeout)

