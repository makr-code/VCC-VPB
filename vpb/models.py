"""Data models for VPB processes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class VPBElement:
    element_id: str
    element_type: str
    name: str
    x: int
    y: int
    description: str = ""
    responsible_authority: str = ""
    legal_basis: str = ""
    deadline_days: int = 0
    geo_reference: str = ""
    ref_file: str = ""
    ref_inline_content: Optional[str] = None
    ref_inline_path: Optional[str] = None
    ref_inline_error: Optional[str] = None
    ref_inline_truncated: bool = False
    ref_source_mtime: Optional[float] = None
    original_element_type: Optional[str] = None
    members: List[str] = field(default_factory=list)
    collapsed: bool = False
    canvas_items: List[int] = field(default_factory=list)

    def center(self) -> Tuple[int, int]:
        return (self.x, self.y)


@dataclass
class VPBConnection:
    connection_id: str
    source_element: str
    target_element: str
    connection_type: str = "SEQUENCE"
    description: str = ""
    arrow_style: str = "single"
    routing_mode: str = "auto"
    canvas_item: Optional[int] = None


__all__ = ["VPBElement", "VPBConnection"]
