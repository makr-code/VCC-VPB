"""Utilities to translate VPB process dictionaries into XML formats."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _slugify(value: Any, default: str) -> str:
    text = _safe_text(value)
    if not text:
        return default
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", text).strip("_")
    return slug or default


def _iter_dicts(items: Iterable[Any]) -> Iterable[Dict[str, Any]]:
    for item in items or []:
        if isinstance(item, dict):
            yield item


def _prettify(root: Element, indent: str) -> str:
    raw = tostring(root, encoding="utf-8")
    pretty = minidom.parseString(raw).toprettyxml(indent=indent)
    lines = [line for line in pretty.splitlines() if line.strip()]
    return "\n".join(lines) + "\n"


def vpb_to_atok_xml(data: Dict[str, Any], *, indent: str = "  ") -> str:
    """Render a VPB process dictionary as ATOK-oriented XML."""

    root = Element("atokProcess")

    metadata_node = SubElement(root, "metadata")
    metadata = data.get("metadata") if isinstance(data, dict) else {}
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            field = SubElement(metadata_node, "field", name=str(key))
            field.text = _safe_text(value)

    elements_node = SubElement(root, "elements")
    for element in _iter_dicts((data or {}).get("elements")):  # type: ignore[union-attr]
        attrs = {
            "id": _safe_text(element.get("element_id")),
            "type": _safe_text(element.get("element_type")),
        }
        name = element.get("name")
        if name:
            attrs["name"] = _safe_text(name)
        element_node = SubElement(elements_node, "element", attrs)

        SubElement(
            element_node,
            "position",
            {
                "x": _safe_text(element.get("x", 0)),
                "y": _safe_text(element.get("y", 0)),
            },
        )

        for optional_key in (
            "description",
            "responsible_authority",
            "legal_basis",
            "deadline_days",
            "group",
            "subprocess",
        ):
            if optional_key in element:
                opt_value = element.get(optional_key)
                if opt_value is not None and opt_value != "":
                    opt_node = SubElement(element_node, optional_key)
                    opt_node.text = _safe_text(opt_value)

    connections_node = SubElement(root, "connections")
    for connection in _iter_dicts((data or {}).get("connections")):  # type: ignore[union-attr]
        attrs = {
            "id": _safe_text(connection.get("connection_id")),
            "type": _safe_text(connection.get("connection_type", "SEQUENCE")),
            "source": _safe_text(connection.get("source_element")),
            "target": _safe_text(connection.get("target_element")),
        }
        connection_node = SubElement(connections_node, "connection", attrs)
        label = connection.get("description") or connection.get("name")
        if label:
            label_node = SubElement(connection_node, "label")
            label_node.text = _safe_text(label)

    return _prettify(root, indent)


def vpb_to_eepk_xml(data: Dict[str, Any], *, indent: str = "  ") -> str:
    """Render a VPB process dictionary as eEPK XML."""

    metadata = data.get("metadata") if isinstance(data, dict) else {}
    process_id = _slugify((metadata or {}).get("id") if isinstance(metadata, dict) else None, "VPB_Process")

    root = Element(
        "eepk:Process",
        {
            "xmlns:eem": "https://vpb.ai/schema/eepk/metadata",
            "xmlns:eepk": "https://vpb.ai/schema/eepk/1.0",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "id": process_id,
            "name": _safe_text((metadata or {}).get("name")) if isinstance(metadata, dict) else "",
        },
    )

    meta_node = SubElement(root, "eem:Metadata")
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            field = SubElement(meta_node, "eem:Field", name=str(key))
            field.text = _safe_text(value)

    elements = list(_iter_dicts((data or {}).get("elements")))  # type: ignore[union-attr]

    events_node = SubElement(root, "eepk:Events")
    functions_node = SubElement(root, "eepk:Functions")
    connectors_node = SubElement(root, "eepk:Connectors")

    layout_node = SubElement(root, "eepk:Layout")

    def _categorise_element(element: Dict[str, Any]) -> str:
        etype = _safe_text(element.get("element_type")).upper()
        if "CONNECTOR" in etype or "GATEWAY" in etype:
            return "connector"
        if etype.endswith("EVENT") or etype.startswith("EVENT") or "EVENT" in etype:
            return "event"
        return "function"

    def _connector_class(element: Dict[str, Any]) -> str:
        etype = _safe_text(element.get("element_type")).upper()
        if "XOR" in etype:
            return "exclusive"
        if "AND" in etype:
            return "parallel"
        if "OR" in etype:
            return "inclusive"
        return "connector"

    for element in elements:
        category = _categorise_element(element)
        attrs = {
            "id": _safe_text(element.get("element_id")),
            "name": _safe_text(element.get("name")),
            "type": _safe_text(element.get("element_type")),
        }

        doc_lines: List[str] = []
        for key in ("description", "responsible_authority", "legal_basis", "deadline_days"):
            value = element.get(key)
            if value not in (None, ""):
                doc_lines.append(f"{key}: {_safe_text(value)}")

        if category == "event":
            node = SubElement(events_node, "eepk:Event", attrs)
        elif category == "connector":
            attrs["class"] = _connector_class(element)
            node = SubElement(connectors_node, "eepk:Connector", attrs)
        else:
            node = SubElement(functions_node, "eepk:Function", attrs)

        if doc_lines:
            documentation = SubElement(node, "eepk:Documentation")
            documentation.text = "\n".join(doc_lines)

        layout_attrs = {
            "ref": _safe_text(element.get("element_id")),
            "x": _safe_text(element.get("x", 0)),
            "y": _safe_text(element.get("y", 0)),
        }
        SubElement(layout_node, "eepk:Node", layout_attrs)

    flows_node = SubElement(root, "eepk:Flows")
    for connection in _iter_dicts((data or {}).get("connections")):  # type: ignore[union-attr]
        attrs = {
            "id": _safe_text(connection.get("connection_id")),
            "source": _safe_text(connection.get("source_element")),
            "target": _safe_text(connection.get("target_element")),
            "type": _safe_text(connection.get("connection_type", "SEQUENCE")),
        }
        flow_node = SubElement(flows_node, "eepk:Flow", attrs)
        label = connection.get("description") or connection.get("name")
        if label:
            SubElement(flow_node, "eepk:Label").text = _safe_text(label)

    return _prettify(root, indent)


def vpb_to_bpmn20_xml(data: Dict[str, Any], *, indent: str = "  ") -> str:
    """Render a VPB process dictionary as BPMN 2.0 compatible XML."""

    metadata = data.get("metadata") if isinstance(data, dict) else {}
    process_id = _slugify((metadata or {}).get("id") if isinstance(metadata, dict) else None, "Process_1")
    definitions_id = f"Definitions_{process_id}"

    root = Element(
        "bpmn:definitions",
        {
            "xmlns:bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
            "xmlns:bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
            "xmlns:dc": "http://www.omg.org/spec/DD/20100524/DC",
            "xmlns:di": "http://www.omg.org/spec/DD/20100524/DI",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "id": definitions_id,
            "targetNamespace": f"https://vpb.ai/process/{process_id}",
        },
    )

    process_name = _safe_text((metadata or {}).get("name")) if isinstance(metadata, dict) else ""
    process_attrs = {"id": process_id or "Process_1", "isExecutable": "false"}
    if process_name:
        process_attrs["name"] = process_name
    process_node = SubElement(root, "bpmn:process", process_attrs)

    documentation_texts: List[str] = []
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            if value in (None, ""):
                continue
            documentation_texts.append(f"{key}: {_safe_text(value)}")
    if documentation_texts:
        documentation = SubElement(process_node, "bpmn:documentation")
        documentation.text = "\n".join(documentation_texts)

    elements = list(_iter_dicts((data or {}).get("elements")))  # type: ignore[union-attr]
    element_index = { _safe_text(e.get("element_id")): e for e in elements }

    def _map_bpmn_element(element: Dict[str, Any]) -> Tuple[str, Dict[str, str]]:
        etype = _safe_text(element.get("element_type")).upper()
        if etype in {"START_EVENT", "START"}:
            return "bpmn:startEvent", {}
        if etype in {"END_EVENT", "TERMINATE_EVENT"}:
            return "bpmn:endEvent", {}
        if "EVENT" in etype:
            return "bpmn:intermediateThrowEvent", {}
        if "XOR" in etype or "EXCLUSIVE" in etype:
            return "bpmn:exclusiveGateway", {}
        if "AND" in etype or "PARALLEL" in etype:
            return "bpmn:parallelGateway", {}
        if "OR" in etype or "INCLUSIVE" in etype:
            return "bpmn:inclusiveGateway", {}
        if "SUB" in etype or etype == "CALL_ACTIVITY":
            attrs: Dict[str, str] = {}
            ref_file = element.get("ref_file")
            if ref_file:
                attrs["calledElement"] = _safe_text(ref_file)
            return "bpmn:callActivity", attrs
        if etype == "GROUP":
            return "bpmn:subProcess", {"triggeredByEvent": "false"}
        return "bpmn:task", {}

    def _documentation_for_element(element: Dict[str, Any]) -> str:
        doc_lines: List[str] = []
        for key in ("description", "responsible_authority", "legal_basis", "deadline_days"):
            value = element.get(key)
            if value in (None, ""):
                continue
            doc_lines.append(f"{key}: {_safe_text(value)}")
        ref = element.get("ref_file")
        if ref:
            doc_lines.append(f"reference: {_safe_text(ref)}")
        return "\n".join(doc_lines)

    for element in elements:
        tag_name, extra_attrs = _map_bpmn_element(element)
        attrs = {"id": _safe_text(element.get("element_id"))}
        name = _safe_text(element.get("name"))
        if name:
            attrs["name"] = name
        attrs.update(extra_attrs)
        node = SubElement(process_node, tag_name, attrs)
        doc = _documentation_for_element(element)
        if doc:
            SubElement(node, "bpmn:documentation").text = doc

    for connection in _iter_dicts((data or {}).get("connections")):  # type: ignore[union-attr]
        attrs = {
            "id": _safe_text(connection.get("connection_id")),
            "sourceRef": _safe_text(connection.get("source_element")),
            "targetRef": _safe_text(connection.get("target_element")),
        }
        label = connection.get("description") or connection.get("name")
        if label:
            attrs["name"] = _safe_text(label)
        SubElement(process_node, "bpmn:sequenceFlow", attrs)

    diagram = SubElement(root, "bpmndi:BPMNDiagram", {"id": f"Diagram_{process_id}"})
    plane = SubElement(
        diagram,
        "bpmndi:BPMNPlane",
        {"id": f"Plane_{process_id}", "bpmnElement": process_attrs["id"]},
    )

    def _bounds_for_element(element: Dict[str, Any]) -> Tuple[float, float]:
        etype = _safe_text(element.get("element_type")).upper()
        if etype in {"START_EVENT", "END_EVENT"} or etype.endswith("EVENT"):
            return 36.0, 36.0
        if "GATEWAY" in etype or "CONNECTOR" in etype:
            return 50.0, 50.0
        if etype == "GROUP" or "SUB" in etype:
            return 160.0, 120.0
        return 120.0, 80.0

    for element in elements:
        element_id = _safe_text(element.get("element_id"))
        width, height = _bounds_for_element(element)
        x = float(element.get("x", 0)) - width / 2
        y = float(element.get("y", 0)) - height / 2
        shape = SubElement(
            plane,
            "bpmndi:BPMNShape",
            {"id": f"BPMNShape_{element_id}", "bpmnElement": element_id},
        )
        SubElement(
            shape,
            "dc:Bounds",
            {
                "x": f"{x:.2f}",
                "y": f"{y:.2f}",
                "width": f"{width:.2f}",
                "height": f"{height:.2f}",
            },
        )

    for connection in _iter_dicts((data or {}).get("connections")):  # type: ignore[union-attr]
        cid = _safe_text(connection.get("connection_id"))
        edge = SubElement(
            plane,
            "bpmndi:BPMNEdge",
            {"id": f"BPMNEdge_{cid}", "bpmnElement": cid},
        )
        src = element_index.get(_safe_text(connection.get("source_element")))
        tgt = element_index.get(_safe_text(connection.get("target_element")))

        def _center(element_dict: Dict[str, Any]) -> Tuple[float, float]:
            return float(element_dict.get("x", 0)), float(element_dict.get("y", 0))

        points: List[Tuple[float, float]] = []
        if src:
            points.append(_center(src))
        if tgt:
            points.append(_center(tgt))
        if not points:
            points = [(0.0, 0.0), (0.0, 0.0)]
        elif len(points) == 1:
            points = [points[0], points[0]]

        for px, py in points:
            SubElement(edge, "di:waypoint", {"x": f"{px:.2f}", "y": f"{py:.2f}"})

    return _prettify(root, indent)


def render_vpb_xml(data: Dict[str, Any], *, format: str, indent: str = "  ") -> str:
    """Render VPB data to the desired XML format."""

    fmt = (format or "atok").lower()
    if fmt in {"atok", "xml"}:
        return vpb_to_atok_xml(data, indent=indent)
    if fmt in {"eepk", "epk"}:
        return vpb_to_eepk_xml(data, indent=indent)
    if fmt in {"bpmn", "bpmn20", "bpmn2", "bpmn_20"}:
        return vpb_to_bpmn20_xml(data, indent=indent)
    raise ValueError(f"Unsupported XML export format: {format}")


__all__ = [
    "vpb_to_atok_xml",
    "vpb_to_eepk_xml",
    "vpb_to_bpmn20_xml",
    "render_vpb_xml",
]
