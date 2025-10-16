from __future__ import annotations

import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from guardrails import GuardrailIssue, run_guardrail_checks, summarize_guardrail_issues

DATASET_PATH = Path(__file__).with_name("testcases.json")
DEFAULT_REPORT_PATH = Path(__file__).parents[2] / "docs" / "AI_Guardrails_Report.md"


def _load_testcases(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Testfall-Datei muss eine Liste enthalten")
    return data


def _normalize_diagram(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "metadata": dict(payload.get("metadata", {}) or {}),
            "elements": [dict(e) for e in (payload.get("elements") or []) if isinstance(e, dict)],
            "connections": [dict(c) for c in (payload.get("connections") or []) if isinstance(c, dict)],
        }
    return {"metadata": {}, "elements": [], "connections": []}


def _evaluate_case(base: Dict[str, Any], diff: Dict[str, Any]) -> Tuple[List[GuardrailIssue], Dict[str, int]]:
    issues = run_guardrail_checks(base, diff=diff)
    summary = summarize_guardrail_issues(issues)
    return issues, summary


def _compare_summary(summary: Dict[str, int], expected: Dict[str, int]) -> Tuple[bool, Dict[str, int]]:
    expected_counts = {"error": 0, "warning": 0, "info": 0}
    expected_counts.update({k: int(v) for k, v in (expected or {}).items() if k in expected_counts})
    deltas = {k: summary.get(k, 0) - expected_counts.get(k, 0) for k in expected_counts}
    success = all(summary.get(k, 0) == expected_counts.get(k, 0) for k in expected_counts)
    return success, deltas


def _issue_rows(issues: Iterable[GuardrailIssue]) -> List[str]:
    rows: List[str] = []
    for issue in issues:
        location_bits = []
        loc = issue.location or {}
        if loc.get("element_id"):
            location_bits.append(f"Element {loc['element_id']}")
        if loc.get("connection_id"):
            location_bits.append(f"Connection {loc['connection_id']}")
        if loc.get("name"):
            location_bits.append(f"Name '{loc['name']}'")
        location_text = f" ({', '.join(location_bits)})" if location_bits else ""
        rows.append(f"- [{issue.severity.upper()}] {issue.code}{location_text}: {issue.message}")
    return rows


def run(output_path: Path = DEFAULT_REPORT_PATH) -> Dict[str, Any]:
    cases = _load_testcases(DATASET_PATH)
    if not cases:
        raise RuntimeError("Keine Guardrail-Testfälle gefunden")

    default_base = _normalize_diagram(cases[0].get("base_diagram"))

    results: List[Dict[str, Any]] = []
    totals = Counter()

    for case in cases:
        base_payload = _normalize_diagram(case.get("base_diagram") or default_base)
        diff_payload = _normalize_diagram(case.get("diff") or {})
        issues, summary = _evaluate_case(base_payload, diff_payload)
        success, deltas = _compare_summary(summary, case.get("expected") or {})
        totals.update(summary)
        results.append(
            {
                "name": case.get("name", "case"),
                "description": case.get("description", ""),
                "summary": summary,
                "success": success,
                "deltas": deltas,
                "issues": [issue.to_dict() for issue in issues],
            }
        )

    totals_dict = {"error": totals.get("error", 0), "warning": totals.get("warning", 0), "info": totals.get("info", 0)}
    totals_dict["cases"] = len(results)

    _write_report(output_path, results, totals_dict)

    return {"results": results, "totals": totals_dict, "report": str(output_path)}


def _write_report(path: Path, results: List[Dict[str, Any]], totals: Dict[str, int]) -> None:
    lines: List[str] = []
    lines.append("# AI Guardrail Evaluation Report")
    lines.append("")
    lines.append("| Testfall | Fehler | Warnungen | Infos | Status |")
    lines.append("|---------|-------:|----------:|------:|:-------|")
    for result in results:
        summary = result["summary"]
        status = "✅" if result["success"] else "⚠️"
        lines.append(
            f"| {result['name']} | {summary.get('error', 0)} | {summary.get('warning', 0)} | {summary.get('info', 0)} | {status} |")
    lines.append("")
    lines.append("## Details")
    lines.append("")
    for result in results:
        lines.append(f"### {result['name']}")
        if result.get("description"):
            lines.append(result["description"])
            lines.append("")
        summary = result["summary"]
        lines.append(
            f"- Fehler: {summary.get('error', 0)} | Warnungen: {summary.get('warning', 0)} | Infos: {summary.get('info', 0)} | Status: {'✅' if result['success'] else '⚠️'}"
        )
        issues_rows = _issue_rows(GuardrailIssue(**issue) for issue in result["issues"])
        if issues_rows:
            lines.extend(issues_rows)
        else:
            lines.append("- Keine Befunde")
        lines.append("")
    lines.append("## Gesamtübersicht")
    lines.append("")
    lines.append(
        f"- Fälle: {totals.get('cases', 0)} | Fehler: {totals.get('error', 0)} | Warnungen: {totals.get('warning', 0)} | Infos: {totals.get('info', 0)}"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    info = run()
    print(json.dumps(info, ensure_ascii=False, indent=2))
