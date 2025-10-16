from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from vpb.styles import CONNECTION_STYLES, ELEMENT_STYLES

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

DEFAULT_NODE_WIDTH = 150.0
DEFAULT_NODE_HEIGHT = 60.0
GROUP_PADDING = 24.0
CANVAS_MARGIN = 60.0
MIN_DIMENSION = 8.0


def _format_number(value: float) -> str:
    formatted = f"{value:.2f}" if abs(value) < 1e7 else f"{value:.0f}"
    while "." in formatted and formatted.endswith("0"):
        formatted = formatted[:-1]
    if formatted.endswith("."):
        formatted = formatted[:-1]
    return formatted or "0"


def _safe_dimension(value: object, default: float) -> float:
    try:
        dim = float(value)
        if dim <= 0:
            raise ValueError
        return dim
    except Exception:
        return default


def _basic_box(element: Dict[str, object]) -> Tuple[float, float, float, float]:
    width = max(_safe_dimension(element.get("width"), DEFAULT_NODE_WIDTH), MIN_DIMENSION)
    height = max(_safe_dimension(element.get("height"), DEFAULT_NODE_HEIGHT), MIN_DIMENSION)
    try:
        cx = float(element.get("x", 0) or 0)
        cy = float(element.get("y", 0) or 0)
    except Exception:
        cx, cy = 0.0, 0.0
    hw = width / 2.0
    hh = height / 2.0
    return (cx - hw, cy - hh, cx + hw, cy + hh)


def _normalize_box(box: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def _expand_box(box: Tuple[float, float, float, float], padding: float) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    return (x0 - padding, y0 - padding, x1 + padding, y1 + padding)


def _box_for_id(
    element_id: str,
    lookup: Dict[str, Dict[str, object]],
    cache: Dict[str, Tuple[float, float, float, float]],
    stack: Set[str],
) -> Tuple[float, float, float, float]:
    if element_id in cache:
        return cache[element_id]
    if element_id in stack:
        return cache.setdefault(element_id, _normalize_box(_basic_box({})))
    element = lookup.get(element_id)
    if not element:
        default_box = _normalize_box((-DEFAULT_NODE_WIDTH / 2, -DEFAULT_NODE_HEIGHT / 2, DEFAULT_NODE_WIDTH / 2, DEFAULT_NODE_HEIGHT / 2))
        cache[element_id] = default_box
        return default_box

    etype = str(element.get("element_type") or "").upper()
    base_box = _normalize_box(_basic_box(element))

    if etype == "GROUP":
        members = []
        raw_members = element.get("members")
        if isinstance(raw_members, (list, tuple)):
            members = [str(mid) for mid in raw_members if mid is not None]
        member_boxes: List[Tuple[float, float, float, float]] = []
        for member_id in members:
            if member_id in stack:
                continue
            member_box = _box_for_id(member_id, lookup, cache, stack | {element_id})
            member_boxes.append(member_box)
        member_boxes = [box for box in member_boxes if box[2] > box[0] and box[3] > box[1]]
        if member_boxes:
            min_x = min(box[0] for box in member_boxes + [base_box])
            min_y = min(box[1] for box in member_boxes + [base_box])
            max_x = max(box[2] for box in member_boxes + [base_box])
            max_y = max(box[3] for box in member_boxes + [base_box])
            group_box = _expand_box((min_x, min_y, max_x, max_y), GROUP_PADDING)
            cache[element_id] = _normalize_box(group_box)
            return cache[element_id]

    cache[element_id] = base_box
    return cache[element_id]


def _offset_box(box: Tuple[float, float, float, float], dx: float, dy: float) -> Tuple[float, float, float, float]:
    x0, y0, x1, y1 = box
    return (x0 + dx, y0 + dy, x1 + dx, y1 + dy)


def _box_center(box: Tuple[float, float, float, float]) -> Tuple[float, float]:
    x0, y0, x1, y1 = box
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


@dataclass
class Point:
    x: float
    y: float

    def to_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass
class SvgElement:
    tag: str
    attrs: Dict[str, str]
    children: List["SvgElement"]
    text: Optional[str] = None

    def to_xml(self) -> ET.Element:
        elem = ET.Element(f"{{{SVG_NS}}}{self.tag}", self.attrs)
        if self.text:
            elem.text = self.text
        for child in self.children:
            elem.append(child.to_xml())
        return elem


def _resolve_element_style(element: Dict[str, object]) -> Dict[str, str]:
    style_name = str(element.get("element_type") or "TASK").upper()
    base = ELEMENT_STYLES.get(style_name, ELEMENT_STYLES.get("TASK", {}))
    fill = base.get("fill")
    outline = base.get("outline")
    shape = (base.get("shape") or "rect").lower()
    dash = base.get("dash")
    dash_tuple: Optional[Tuple[int, ...]] = None
    if isinstance(dash, (list, tuple)):
        try:
            dash_tuple = tuple(int(v) for v in dash)
        except Exception:
            dash_tuple = None
    return {
        "fill": fill if fill not in ("", None) else "none",
        "stroke": outline if outline not in ("", None) else "none",
        "shape": shape,
        "dash": dash_tuple,
    }


def _shape_path(element: Dict[str, object], box: Tuple[float, float, float, float]) -> tuple[str, Dict[str, str]]:
    x0, y0, x1, y1 = box
    width = max(1.0, x1 - x0)
    height = max(1.0, y1 - y0)
    cx, cy = _box_center(box)
    style = _resolve_element_style(element)
    shape = style.get("shape", "rect")
    dash = style.get("dash")
    dash_str = ",".join(str(v) for v in dash) if dash else None
    fill = style.get("fill", "none")
    stroke = style.get("stroke", "none")

    common_attrs = {
        "fill": fill,
        "stroke": stroke,
        "stroke-width": "2",
    }
    if dash_str:
        common_attrs["stroke-dasharray"] = dash_str

    if shape in {"oval", "circle"}:
        attrs = {
            **common_attrs,
            "cx": _format_number(cx),
            "cy": _format_number(cy),
            "rx": _format_number(width / 2.0),
            "ry": _format_number(height / 2.0),
        }
        return "ellipse", attrs
    if shape == "diamond":
        hw = width / 2.0
        hh = height / 2.0
        points = [
            (cx, cy - hh),
            (cx + hw, cy),
            (cx, cy + hh),
            (cx - hw, cy),
        ]
        attr_points = " ".join(f"{_format_number(x)},{_format_number(y)}" for x, y in points)
        attrs = {**common_attrs, "points": attr_points}
        return "polygon", attrs
    if shape == "hex":
        hw = width / 2.0
        hh = height / 2.0
        points = [
            (cx - hw / 2.0, cy - hh),
            (cx + hw / 2.0, cy - hh),
            (cx + hw, cy),
            (cx + hw / 2.0, cy + hh),
            (cx - hw / 2.0, cy + hh),
            (cx - hw, cy),
        ]
        attr_points = " ".join(f"{_format_number(x)},{_format_number(y)}" for x, y in points)
        attrs = {**common_attrs, "points": attr_points}
        return "polygon", attrs

    attrs = {
        **common_attrs,
        "x": _format_number(x0),
        "y": _format_number(y0),
        "width": _format_number(width),
        "height": _format_number(height),
    }
    if shape == "rect":
        attrs["rx"] = _format_number(min(12.0, width / 6.0))
        attrs["ry"] = _format_number(min(12.0, height / 6.0))
    return "rect", attrs


def _element_label(element: Dict[str, object], box: Tuple[float, float, float, float]) -> SvgElement:
    cx, cy = _box_center(box)
    name = str(element.get("name") or "")
    label = SvgElement(
        tag="text",
        attrs={
            "x": _format_number(cx),
            "y": _format_number(cy),
            "font-family": "Segoe UI",
            "font-size": "14",
            "text-anchor": "middle",
            "fill": "#1f1f1f",
            "dominant-baseline": "middle",
        },
        children=[],
        text=name,
    )
    return label


def _polyline(points: Sequence[Point], *, stroke: str = "#000000", width: float = 2.0, dash: Optional[str] = None) -> SvgElement:
    d = " ".join(f"{_format_number(p.x)},{_format_number(p.y)}" for p in points)
    attrs = {
        "points": d,
        "fill": "none",
        "stroke": stroke,
        "stroke-width": _format_number(width),
    }
    if dash:
        attrs["stroke-dasharray"] = dash
    return SvgElement(tag="polyline", attrs=attrs, children=[])


def _connection_arrow(points: Sequence[Point], stroke: str, *, position: str = "end") -> Optional[SvgElement]:
    if len(points) < 2:
        return None
    if position == "start":
        tip = points[0]
        ref = points[1]
    else:
        tip = points[-1]
        ref = points[-2]
    import math

    angle = math.atan2(tip.y - ref.y, tip.x - ref.x)
    size = 10.0
    left = Point(tip.x - size * math.cos(angle - math.pi / 6), tip.y - size * math.sin(angle - math.pi / 6))
    right = Point(tip.x - size * math.cos(angle + math.pi / 6), tip.y - size * math.sin(angle + math.pi / 6))
    attrs = {
        "points": " ".join(
            [
                f"{_format_number(tip.x)},{_format_number(tip.y)}",
                f"{_format_number(left.x)},{_format_number(left.y)}",
                f"{_format_number(right.x)},{_format_number(right.y)}",
            ]
        ),
        "fill": stroke,
        "stroke": stroke,
    }
    return SvgElement(tag="polygon", attrs=attrs, children=[])


def _render_connections(
    connections: Iterable[Dict[str, object]],
    element_lookup: Dict[str, Dict[str, object]],
    box_lookup: Dict[str, Tuple[float, float, float, float]],
    dx: float,
    dy: float,
) -> List[SvgElement]:
    svg_items: List[SvgElement] = []
    for conn in connections:
        src_id = conn.get("source_element")
        tgt_id = conn.get("target_element")
        if not src_id or not tgt_id:
            continue
        src = element_lookup.get(str(src_id))
        tgt = element_lookup.get(str(tgt_id))
        if not src or not tgt:
            continue
        src_box = box_lookup.get(str(src.get("element_id"))) or _normalize_box(_basic_box(src))
        tgt_box = box_lookup.get(str(tgt.get("element_id"))) or _normalize_box(_basic_box(tgt))
        sx, sy = _box_center(src_box)
        tx, ty = _box_center(tgt_box)
        horizontal = abs(tx - sx) >= abs(ty - sy)

        if horizontal:
            start_x = src_box[2] if tx >= sx else src_box[0]
            end_x = tgt_box[0] if tx >= sx else tgt_box[2]
            start_y = sy
            end_y = ty
            mid_x = (start_x + end_x) / 2.0
            points_model = [
                (start_x, start_y),
                (mid_x, start_y),
                (mid_x, end_y),
                (end_x, end_y),
            ]
        else:
            start_y = src_box[3] if ty >= sy else src_box[1]
            end_y = tgt_box[1] if ty >= sy else tgt_box[3]
            start_x = sx
            end_x = tx
            mid_y = (start_y + end_y) / 2.0
            points_model = [
                (start_x, start_y),
                (start_x, mid_y),
                (end_x, mid_y),
                (end_x, end_y),
            ]

        # Degenerate fallback (z. B. identische Start-/Endpunkte)
        points_model = [points_model[0]] + [pt for idx, pt in enumerate(points_model[1:], start=1) if pt != points_model[idx - 1]]
        if len(points_model) < 2:
            points_model = [(sx, sy), (tx, ty)]

        mapped_points = [Point(px + dx, py + dy) for px, py in points_model]
        style = CONNECTION_STYLES.get(str(conn.get("connection_type") or "SEQUENCE"), {})
        stroke = style.get("fill", "#000000")
        dash = None
        if style.get("dash"):
            try:
                dash = ",".join(str(int(v)) for v in style["dash"])
            except Exception:
                dash = None
        poly = _polyline(mapped_points, stroke=stroke, width=float(style.get("width", 2)), dash=dash)
        svg_items.append(poly)
        arrow_style = str(conn.get("arrow_style") or "single")
        arrow_style_lower = arrow_style.lower()
        if arrow_style_lower != "none":
            arrow_end = _connection_arrow(mapped_points, stroke, position="end")
            if arrow_end:
                svg_items.append(arrow_end)
            if arrow_style_lower == "double":
                arrow_start = _connection_arrow(mapped_points, stroke, position="start")
                if arrow_start:
                    svg_items.append(arrow_start)
    return svg_items


def render_process_svg(process_data: Dict[str, object]) -> str:
    metadata = process_data.get("metadata") or {}
    elements = process_data.get("elements") or []
    connections = process_data.get("connections") or []
    element_lookup = {str(el.get("element_id")): el for el in elements if el.get("element_id")}
    box_cache: Dict[str, Tuple[float, float, float, float]] = {}
    element_boxes: List[Tuple[Dict[str, object], Tuple[float, float, float, float]]] = []
    for element in elements:
        element_id = element.get("element_id")
        if element_id is not None:
            box = _box_for_id(str(element_id), element_lookup, box_cache, set())
        else:
            box = _normalize_box(_basic_box(element))
        element_boxes.append((element, box))

    if element_boxes:
        min_x = min(box[0] for _, box in element_boxes)
        min_y = min(box[1] for _, box in element_boxes)
        max_x = max(box[2] for _, box in element_boxes)
        max_y = max(box[3] for _, box in element_boxes)
    else:
        default_box = _normalize_box(_basic_box({}))
        min_x, min_y, max_x, max_y = default_box

    min_x -= CANVAS_MARGIN
    min_y -= CANVAS_MARGIN
    max_x += CANVAS_MARGIN
    max_y += CANVAS_MARGIN

    width = max(MIN_DIMENSION, max_x - min_x)
    height = max(MIN_DIMENSION, max_y - min_y)
    offset_x = -min_x
    offset_y = -min_y
    view_box = f"0 0 {_format_number(width)} {_format_number(height)}"

    root = SvgElement(
        tag="svg",
        attrs={
            "version": "1.1",
            "viewBox": view_box,
            "width": _format_number(width),
            "height": _format_number(height),
        },
        children=[],
    )

    # Hintergrund
    root.children.append(
        SvgElement(
            tag="rect",
            attrs={
                "x": "0",
                "y": "0",
                "width": _format_number(width),
                "height": _format_number(height),
                "fill": "#ffffff",
            },
            children=[],
        )
    )

    box_lookup: Dict[str, Tuple[float, float, float, float]] = {}

    for element, box in element_boxes:
        box_svg = _offset_box(box, offset_x, offset_y)
        element_id = element.get("element_id")
        if element_id is not None:
            box_lookup[str(element_id)] = box
        tag, attrs = _shape_path(element, box_svg)
        root.children.append(SvgElement(tag=tag, attrs=attrs, children=[]))
        name = str(element.get("name") or "").strip()
        if name:
            root.children.append(_element_label(element, box_svg))

    root.children.extend(_render_connections(connections, element_lookup, box_lookup, offset_x, offset_y))

    title = str(metadata.get("name") or "").strip()
    if title:
        root.children.append(
            SvgElement(
                tag="text",
                attrs={
                    "x": _format_number(20.0),
                    "y": _format_number(28.0),
                    "font-family": "Segoe UI",
                    "font-size": "18",
                    "font-weight": "600",
                    "fill": "#1f1f1f",
                },
                children=[],
                text=title,
            )
        )

    subtitle_bits: List[str] = []
    version = str(metadata.get("version") or "").strip()
    owner = str(metadata.get("owner") or "").strip()
    if version:
        subtitle_bits.append(f"Version: {version}")
    if owner:
        subtitle_bits.append(f"Verantwortlich: {owner}")
    if subtitle_bits:
        root.children.append(
            SvgElement(
                tag="text",
                attrs={
                    "x": _format_number(20.0),
                    "y": _format_number(48.0),
                    "font-family": "Segoe UI",
                    "font-size": "12",
                    "fill": "#555555",
                },
                children=[],
                text=" | ".join(subtitle_bits),
            )
        )

    tree = ET.ElementTree(root.to_xml())
    import io

    buffer = io.BytesIO()
    tree.write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue().decode("utf-8")
