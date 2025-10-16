"""Arrangement panel widgets for layout actions."""

from __future__ import annotations

from typing import Callable, Iterable, List, Sequence, Tuple

import tkinter as tk

__all__ = ["ArrangePanel"]


Action = Tuple[str, Callable[[], None]]
Section = Tuple[str, Sequence[Action]]


class ArrangePanel(tk.Frame):
    """Compact panel offering layout/arrangement shortcuts."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        sections: Iterable[Section] | None = None,
        max_columns: int = 2,
    ) -> None:
        super().__init__(master, bg="#f7f7f7", relief=tk.GROOVE, borderwidth=1)
        self._max_columns = max(1, int(max_columns))
        header = tk.Frame(self, bg="#f0f0f0")
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="Bearbeitung", bg="#f0f0f0", font=("Segoe UI", 10, "bold")).pack(
            side=tk.LEFT, padx=6, pady=6
        )
        self._body = tk.Frame(self, bg="#f7f7f7")
        self._body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._sections: List[Tuple[tk.LabelFrame, List[tk.Button]]] = []
        if sections:
            self.render(sections)

    def clear(self) -> None:
        for frame, buttons in self._sections:
            for btn in buttons:
                try:
                    btn.destroy()
                except Exception:
                    pass
            try:
                frame.destroy()
            except Exception:
                pass
        self._sections.clear()

    def render(self, sections: Iterable[Section]) -> None:
        self.clear()
        for index, section in enumerate(sections):
            try:
                title, actions = section
            except Exception:
                continue
            if not actions:
                continue
            frame = tk.LabelFrame(self._body, text=str(title), bg="#f7f7f7", padx=6, pady=4)
            frame.pack(fill=tk.X, padx=8, pady=(6 if index == 0 else 2, 6))
            buttons: List[tk.Button] = []
            for idx, (label, command) in enumerate(actions):
                btn = tk.Button(frame, text=str(label), command=command)
                row = idx // self._max_columns
                col = idx % self._max_columns
                btn.grid(row=row, column=col, padx=3, pady=3, sticky="we")
                try:
                    frame.columnconfigure(col, weight=1)
                except Exception:
                    pass
                buttons.append(btn)
            self._sections.append((frame, buttons))

    def set_actions(self, sections: Iterable[Section]) -> None:
        self.render(sections)
