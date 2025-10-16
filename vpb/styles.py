"""Styling defaults for VPB elements and connections."""

from __future__ import annotations

from typing import Dict

ELEMENT_STYLES: Dict[str, Dict] = {
    "EVENT": {"shape": "oval", "fill": "#FFE6E6", "outline": "#CC0000"},
    "FUNCTION": {"shape": "rect", "fill": "#E6F3FF", "outline": "#004C99"},
    "ORGANIZATION_UNIT": {"shape": "rect", "fill": "#F0F0F0", "outline": "#666666"},
    "INFORMATION_OBJECT": {"shape": "diamond", "fill": "#FFFFCC", "outline": "#999900"},
    "AND_CONNECTOR": {"shape": "circle", "fill": "#E6FFE6", "outline": "#00AA00"},
    "OR_CONNECTOR": {"shape": "circle", "fill": "#FFE6CC", "outline": "#CC6600"},
    "XOR_CONNECTOR": {"shape": "diamond", "fill": "#FFCCCC", "outline": "#CC0000"},
    "START_EVENT": {"shape": "circle", "fill": "#90EE90", "outline": "#2E8B57"},
    "END_EVENT": {"shape": "circle", "fill": "#FFB6C1", "outline": "#B22222"},
    "GATEWAY": {"shape": "diamond", "fill": "#FFFF99", "outline": "#B3B300"},
    "LEGAL_CHECKPOINT": {"shape": "hex", "fill": "#E6E6FA", "outline": "#6A5ACD"},
    "DEADLINE": {"shape": "rect", "fill": "#FFA07A", "outline": "#CD5C5C"},
    "COMPETENCY_CHECK": {"shape": "rect", "fill": "#DDA0DD", "outline": "#9932CC"},
    "GEO_CONTEXT": {"shape": "rect", "fill": "#87CEEB", "outline": "#4682B4"},
    "SUBPROCESS": {"shape": "rect", "fill": "#F9F9F9", "outline": "#444444", "dash": (4, 4)},
    "GROUP": {"shape": "rect", "fill": "", "outline": "#666666", "dash": (6, 4)},
}

CONNECTION_STYLES: Dict[str, Dict] = {
    "SEQUENCE": {"fill": "#000000", "width": 2, "dash": None},
    "MESSAGE": {"fill": "#0066CC", "width": 2, "dash": (6, 6)},
    "ASSOCIATION": {"fill": "#666666", "width": 1, "dash": (2, 6)},
    "LEGAL": {"fill": "#8B0000", "width": 3, "dash": None},
    "APPROVAL": {"fill": "#008000", "width": 2, "dash": None},
    "REJECTION": {"fill": "#FF0000", "width": 2, "dash": None},
    "DOCUMENT": {"fill": "#4B0082", "width": 2, "dash": (6, 6)},
    "NOTIFICATION": {"fill": "#FF8C00", "width": 2, "dash": (6, 6)},
    "DEADLINE": {"fill": "#DC143C", "width": 2, "dash": (2, 6)},
    "ESCALATION": {"fill": "#B22222", "width": 3, "dash": None},
    "GEO_REF": {"fill": "#20B2AA", "width": 2, "dash": (2, 6)},
}

__all__ = ["ELEMENT_STYLES", "CONNECTION_STYLES"]
