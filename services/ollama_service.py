"""OllamaService abstrahiert Chat-/Completion-Aufrufe.

Bietet zwei Modi:
- sync_chat(payload) -> str (oder Iterator[str] für Streaming)
- stream_chat(payload) -> Iterator[str]

Payload Felder:
- endpoint, model, temperature, num_predict, messages
"""
from __future__ import annotations
from typing import Iterator, List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - nur zur Typprüfung
    from controller.app_controller import TaskContext

try:
    from ollama_client import OllamaClient, OllamaOptions  # type: ignore
except Exception:  # pragma: no cover
    OllamaClient = None  # type: ignore
    OllamaOptions = None  # type: ignore

def _ctx_check(context: "TaskContext | None") -> None:
    if context is None:
        return
    check = getattr(context, "check_cancelled", None)
    if callable(check):
        check()


def _ctx_progress(context: "TaskContext | None", *, fraction: Optional[float] = None, message: Optional[str] = None, **fields: Any) -> None:
    if context is None:
        return
    publish = getattr(context, "publish_progress", None)
    if callable(publish):
        try:
            publish(fraction=fraction, message=message, **fields)
        except Exception:
            pass


class OllamaService:
    def chat_stream(self, payload: Dict[str, Any], context: "TaskContext | None" = None) -> Iterator[str]:
        if not OllamaClient:
            yield "[OllamaClient nicht verfügbar]"
            return
        endpoint = payload.get("endpoint")
        model = payload.get("model")
        temperature = float(payload.get("temperature", 0.2))
        num_predict = int(payload.get("num_predict", 400))
        messages: List[Dict[str, str]] = payload.get("messages") or []
        client = OllamaClient(endpoint=endpoint, model=model)
        opts = OllamaOptions(temperature=temperature, num_predict=num_predict)
        _ctx_progress(context, fraction=0.0, message="LLM Anfrage gesendet")
        _ctx_check(context)
        chunk_count = 0
        for chunk in client.chat_stream(messages, options=opts):
            chunk_count += 1
            _ctx_check(context)
            if chunk_count == 1 or (chunk_count % 5 == 0):
                _ctx_progress(
                    context,
                    message="LLM antwortet",
                    fraction=min(0.2 + chunk_count / 100.0, 0.9),
                    chunks=chunk_count,
                )
            yield chunk
        _ctx_progress(context, fraction=1.0, message="LLM Antwort vollständig", chunks=chunk_count)

    def chat(self, payload: Dict[str, Any], context: "TaskContext | None" = None) -> str:
        return "".join(self.chat_stream(payload, context=context))
