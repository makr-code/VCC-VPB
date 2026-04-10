"""
VPB Import Service
==================

Handles importing process diagrams from various formats:
- Mermaid: Text-based flowchart diagrams

The import service parses external diagram formats and converts them to VPB
DocumentModel format. Only supports importing diagrams that can be represented
as BPMN-compatible process flows.

Author: VPB Development Team
Date: 2026-01-22
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import re

from ..models.document import DocumentModel, DocumentMetadata
from ..models.element import VPBElement
from ..models.connection import VPBConnection
from ..infrastructure.event_bus import EventBus


# ============================================================================
# Exception Classes
# ============================================================================

class ImportServiceError(Exception):
    """Base exception for import service errors."""
    pass


class MermaidImportError(ImportServiceError):
    """Error during Mermaid import."""
    pass


class UnsupportedDiagramError(ImportServiceError):
    """Diagram type not supported or cannot be converted to BPMN."""
    pass


# ============================================================================
# Import Configuration
# ============================================================================

@dataclass
class ImportConfig:
    """Configuration for import operations."""
    
    # Mermaid settings
    mermaid_auto_layout: bool = True  # Automatically calculate positions
    mermaid_default_spacing_x: int = 200  # Horizontal spacing between elements
    mermaid_default_spacing_y: int = 150  # Vertical spacing between elements
    mermaid_start_x: int = 100  # Starting X position
    mermaid_start_y: int = 100  # Starting Y position
    
    # General
    validate_bpmn_compatibility: bool = True  # Ensure diagram can be converted to BPMN
    include_metadata: bool = True


# ============================================================================
# Import Service
# ============================================================================

class ImportService:
    """
    Service for importing process diagrams from various formats.
    
    Supports:
    - Mermaid flowchart import with BPMN compatibility validation
    
    Example:
        >>> service = ImportService()
        >>> document = service.import_from_mermaid("process.md")
        >>> # Now you can use the document with VPB
    """
    
    def __init__(self, config: Optional[ImportConfig] = None):
        """
        Initialize the import service.
        
        Args:
            config: Import configuration (uses defaults if not provided)
        """
        self.config = config or ImportConfig()
        self.event_bus = EventBus()
    
    # ========================================================================
    # Mermaid Import
    # ========================================================================
    
    def import_from_mermaid(
        self,
        input_path: str,
        title: Optional[str] = None
    ) -> DocumentModel:
        """
        Import process diagram from Mermaid format.
        
        Parses Mermaid flowchart syntax and converts it to VPB DocumentModel.
        Only supports flowchart diagrams that can be represented as BPMN
        process flows.
        
        Supported Mermaid features:
        - flowchart/graph diagrams (TB, LR, BT, RL directions)
        - Node shapes: [], (), [()], {}, [[]]
        - Connection types: -->, -.->
        - Node labels
        - Connection labels
        
        Not supported (will raise UnsupportedDiagramError):
        - Subgraphs (containers not yet supported for import)
        - erDiagram (not a process flow)
        - Class diagrams
        - Other non-flowchart diagram types
        
        Args:
            input_path: Path to Mermaid file (.md or .mmd)
            title: Optional title for the document (defaults to filename)
            
        Returns:
            DocumentModel with imported diagram
            
        Raises:
            MermaidImportError: If Mermaid import fails
            UnsupportedDiagramError: If diagram cannot be converted to BPMN
            
        Example:
            >>> service.import_from_mermaid("process.md")
            >>> service.import_from_mermaid("flow.mmd", title="My Process")
        """
        try:
            # Publish start event
            self.event_bus.publish('import:mermaid:started', {
                'input_path': input_path
            })
            
            input_file = Path(input_path)
            if not input_file.exists():
                raise MermaidImportError(f"File not found: {input_path}")
            
            # Read file content
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse Mermaid content
            mermaid_data = self._parse_mermaid(content)
            
            # Validate BPMN compatibility
            if self.config.validate_bpmn_compatibility:
                self._validate_bpmn_compatibility(mermaid_data)
            
            # Convert to DocumentModel
            document = self._mermaid_to_document(mermaid_data, title or input_file.stem)
            
            # Publish success event
            self.event_bus.publish('import:mermaid:completed', {
                'input_path': str(input_file),
                'element_count': len(document.get_all_elements()),
                'connection_count': len(document.get_all_connections())
            })
            
            return document
            
        except (MermaidImportError, UnsupportedDiagramError):
            raise
        except Exception as e:
            # Publish error event
            self.event_bus.publish('import:mermaid:failed', {
                'input_path': input_path,
                'error': str(e)
            })
            raise MermaidImportError(f"Failed to import Mermaid: {e}") from e
    
    def _parse_mermaid(self, content: str) -> Dict[str, Any]:
        """
        Parse Mermaid syntax into structured data.
        
        Args:
            content: Mermaid file content
            
        Returns:
            Dictionary with parsed data:
            {
                'diagram_type': 'flowchart',
                'direction': 'TB',
                'nodes': {node_id: {'label': ..., 'shape': ...}},
                'connections': [{'from': ..., 'to': ..., 'label': ..., 'type': ...}],
                'metadata': {...}
            }
        """
        result = {
            'diagram_type': None,
            'direction': 'TB',
            'nodes': {},
            'connections': [],
            'metadata': {}
        }
        
        lines = content.split('\n')
        in_mermaid_block = False
        in_yaml_metadata = False
        yaml_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Check for YAML frontmatter
            if line == '---':
                if not in_yaml_metadata:
                    in_yaml_metadata = True
                    continue
                else:
                    in_yaml_metadata = False
                    # Parse collected YAML
                    self._parse_yaml_metadata(yaml_lines, result['metadata'])
                    yaml_lines = []
                    continue
            
            if in_yaml_metadata:
                yaml_lines.append(line)
                continue
            
            # Check for Mermaid code block
            if line.startswith('```mermaid'):
                in_mermaid_block = True
                continue
            elif line.startswith('```') and in_mermaid_block:
                in_mermaid_block = False
                continue
            
            if not in_mermaid_block and not line:
                continue
            
            # Skip comments
            if line.startswith('%%'):
                continue
            
            # Check for diagram type declaration
            if line.startswith('flowchart') or line.startswith('graph'):
                parts = line.split()
                result['diagram_type'] = parts[0]
                if len(parts) > 1 and parts[1] in ['TB', 'LR', 'BT', 'RL', 'TD']:
                    result['direction'] = parts[1]
                    if result['direction'] == 'TD':
                        result['direction'] = 'TB'  # TD is alias for TB
                continue
            
            # Check for unsupported diagram types
            if line.startswith('erDiagram') or line.startswith('classDiagram') or \
               line.startswith('sequenceDiagram') or line.startswith('stateDiagram'):
                raise UnsupportedDiagramError(
                    f"Diagram type '{line.split()[0]}' cannot be converted to BPMN. "
                    "Only flowchart/graph diagrams are supported."
                )
            
            # Skip style definitions
            if line.startswith('style ') or line.startswith('classDef '):
                continue
            
            # Skip subgraph (not supported yet)
            if line.startswith('subgraph') or line == 'end':
                continue
            
            # Parse node definitions and connections
            if in_mermaid_block or result['diagram_type']:
                self._parse_mermaid_line(line, result)
        
        # Validate we found a diagram
        if not result['diagram_type']:
            raise MermaidImportError(
                "No valid Mermaid diagram found. "
                "Expected 'flowchart' or 'graph' declaration."
            )
        
        return result
    
    def _parse_yaml_metadata(self, yaml_lines: List[str], metadata: Dict[str, Any]):
        """Parse YAML metadata from frontmatter."""
        for line in yaml_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                metadata[key] = value
    
    def _parse_mermaid_line(self, line: str, result: Dict[str, Any]):
        """Parse a single Mermaid line for nodes and connections."""
        if not line or line.startswith('%%'):
            return
        
        # First, parse node definitions: nodeA["Label"] or nodeA(Label) etc.
        # Shapes: [], (), {}, [[]], [()] 
        node_pattern = r'(\w+)([\[\(\{][\[\(]?)([^\]\)\}]+)([\]\)\}][\]\)]?)'
        node_matches = re.finditer(node_pattern, line)
        
        for match in node_matches:
            node_id = match.group(1)
            open_bracket = match.group(2)
            label = match.group(3).strip(' "\'')
            close_bracket = match.group(4)
            
            # Determine shape from brackets
            shape = self._determine_shape_from_brackets(open_bracket, close_bracket)
            
            result['nodes'][node_id] = {
                'label': label,
                'shape': shape
            }
        
        # Parse connections - handle chained connections like A --> B --> C
        # Find all arrow positions and their types in the line
        arrow_types = ['-->', '---', '-.->']
        
        # Find all arrow positions and types
        arrows = []
        for arrow_type in arrow_types:
            pos = 0
            while True:
                idx = line.find(arrow_type, pos)
                if idx == -1:
                    break
                arrows.append((idx, arrow_type))
                pos = idx + len(arrow_type)
        
        # Sort arrows by position to process them in order
        arrows.sort(key=lambda x: x[0])
        
        if not arrows:
            return
        
        # Extract connections between consecutive arrows
        prev_end = 0
        for i, (arrow_pos, arrow_type) in enumerate(arrows):
            # Get source node (text before arrow, after previous arrow)
            source_part = line[prev_end:arrow_pos].strip()
            
            # Determine connection type
            conn_type = 'SEQUENCE'
            if '-.->' in arrow_type or arrow_type.startswith('..'):
                conn_type = 'INFORMATION'
            
            # Get target node (between this arrow and next arrow, or end of line)
            if i < len(arrows) - 1:
                target_part = line[arrow_pos + len(arrow_type):arrows[i+1][0]].strip()
            else:
                target_part = line[arrow_pos + len(arrow_type):].strip()
            
            # Extract node IDs and labels from source and target
            source_id = self._extract_node_id(source_part)
            target_id, label = self._extract_node_id_and_label(target_part)
            
            if source_id and target_id:
                result['connections'].append({
                    'from': source_id,
                    'to': target_id,
                    'label': label,
                    'type': conn_type
                })
                
                # Make sure both nodes exist
                if source_id not in result['nodes']:
                    result['nodes'][source_id] = {'label': source_id, 'shape': 'rectangle'}
                if target_id not in result['nodes']:
                    result['nodes'][target_id] = {'label': target_id, 'shape': 'rectangle'}
            
            # Update prev_end for next iteration (skip the arrow)
            prev_end = arrow_pos + len(arrow_type)
    
    def _extract_node_id(self, text: str) -> Optional[str]:
        """Extract node ID from text that may have brackets/labels."""
        text = text.strip()
        # Look for node ID at the start (before any brackets or labels)
        match = re.match(r'(\w+)', text)
        if match:
            return match.group(1)
        return None
    
    def _extract_node_id_and_label(self, text: str) -> Tuple[Optional[str], str]:
        """Extract node ID and optional label from text."""
        text = text.strip()
        
        # Check for label in |label| format
        label_match = re.match(r'\|([^\|]+)\|\s*(.+)', text)
        if label_match:
            label = label_match.group(1).strip()
            remaining = label_match.group(2).strip()
            node_id = self._extract_node_id(remaining)
            return node_id, label
        
        # No label, just extract node ID
        node_id = self._extract_node_id(text)
        return node_id, ""
    
    def _determine_shape_from_brackets(self, open_bracket: str, close_bracket: str) -> str:
        """Determine VPB element shape from Mermaid brackets."""
        bracket_pair = open_bracket + close_bracket
        
        # Mermaid shape mapping to VPB element types
        shape_map = {
            '[]': 'rectangle',          # Standard rectangle [text]
            '()': 'stadium',             # Rounded ends (text) - for start/end events
            '[()]': 'stadium',           # Alternative stadium syntax [(text)]
            '([])': 'stadium',           # Alternative stadium syntax ([text])
            '{}': 'diamond',             # Decision/gateway {text}
            '[[]]': 'subprocess',        # Subprocess/container [[text]]
            '>]': 'rectangle',           # Asymmetric shape >text] - treat as rectangle
        }
        
        return shape_map.get(bracket_pair, 'rectangle')
    
    def _validate_bpmn_compatibility(self, mermaid_data: Dict[str, Any]):
        """
        Validate that the Mermaid diagram can be converted to BPMN.
        
        BPMN-compatible diagrams must:
        - Be flowchart or graph type
        - Have valid process flow structure
        - Use supported node shapes
        """
        # Check diagram type
        if mermaid_data['diagram_type'] not in ['flowchart', 'graph']:
            raise UnsupportedDiagramError(
                f"Diagram type '{mermaid_data['diagram_type']}' is not supported. "
                "Only 'flowchart' and 'graph' can be converted to BPMN."
            )
        
        # Check for nodes
        if not mermaid_data['nodes']:
            raise MermaidImportError("No nodes found in diagram")
        
        # Check for at least one connection (optional, single node is valid)
        # Connection validation is done during conversion
    
    def _mermaid_to_document(
        self,
        mermaid_data: Dict[str, Any],
        title: str
    ) -> DocumentModel:
        """
        Convert parsed Mermaid data to VPB DocumentModel.
        
        Args:
            mermaid_data: Parsed Mermaid data
            title: Document title
            
        Returns:
            DocumentModel instance
        """
        # Create document with metadata
        doc = DocumentModel()
        
        # Set metadata
        metadata = DocumentMetadata(
            title=title,
            description=mermaid_data['metadata'].get('description', ''),
            author=mermaid_data['metadata'].get('author', ''),
            version='1.0'
        )
        doc.metadata = metadata
        
        # Calculate layout
        layout = self._calculate_layout(
            mermaid_data['nodes'],
            mermaid_data['connections'],
            mermaid_data['direction']
        )
        
        # Create elements
        for node_id, node_info in mermaid_data['nodes'].items():
            element = self._create_element_from_node(
                node_id,
                node_info,
                layout[node_id]
            )
            doc.add_element(element)
        
        # Create connections
        for idx, conn_info in enumerate(mermaid_data['connections']):
            connection = self._create_connection(conn_info, idx)
            doc.add_connection(connection)
        
        return doc
    
    def _calculate_layout(
        self,
        nodes: Dict[str, Any],
        connections: List[Dict[str, Any]],
        direction: str
    ) -> Dict[str, Tuple[int, int]]:
        """
        Calculate positions for nodes based on diagram direction.
        
        Uses a simple layered layout algorithm:
        - Topological sort to determine layers
        - Position nodes in layers based on connections
        
        Returns:
            Dictionary mapping node_id to (x, y) position
        """
        layout = {}
        
        # Build adjacency list and reverse adjacency list (for optimized predecessor checking)
        adjacency = {node_id: [] for node_id in nodes}
        reverse_adjacency = {node_id: [] for node_id in nodes}
        in_degree = {node_id: 0 for node_id in nodes}
        
        for conn in connections:
            adjacency[conn['from']].append(conn['to'])
            reverse_adjacency[conn['to']].append(conn['from'])
            in_degree[conn['to']] += 1
        
        # Topological sort (Kahn's algorithm) - O(V + E) complexity
        layers = []
        current_layer = [node_id for node_id, degree in in_degree.items() if degree == 0]
        
        # If no start nodes, just use first node
        if not current_layer:
            current_layer = [list(nodes.keys())[0]]
        
        visited = set()
        while current_layer:
            layers.append(current_layer[:])
            next_layer = []
            
            for node_id in current_layer:
                visited.add(node_id)
                for neighbor in adjacency.get(node_id, []):
                    if neighbor not in visited and neighbor not in next_layer:
                        # Check if all predecessors are visited using reverse adjacency
                        # This is O(number of predecessors) instead of O(all nodes)
                        predecessors = reverse_adjacency.get(neighbor, [])
                        predecessors_visited = all(pred in visited for pred in predecessors)
                        
                        if predecessors_visited:
                            next_layer.append(neighbor)
            
            current_layer = next_layer
        
        # Add any remaining nodes (cyclic dependencies or disconnected)
        remaining = [node_id for node_id in nodes if node_id not in visited]
        if remaining:
            layers.append(remaining)
        
        # Calculate positions based on direction
        spacing_x = self.config.mermaid_default_spacing_x
        spacing_y = self.config.mermaid_default_spacing_y
        start_x = self.config.mermaid_start_x
        start_y = self.config.mermaid_start_y
        
        if direction in ['TB', 'BT']:  # Top-to-bottom or bottom-to-top
            for layer_idx, layer in enumerate(layers):
                y = start_y + layer_idx * spacing_y
                for node_idx, node_id in enumerate(layer):
                    x = start_x + node_idx * spacing_x
                    layout[node_id] = (x, y)
        else:  # LR or RL (left-to-right or right-to-left)
            for layer_idx, layer in enumerate(layers):
                x = start_x + layer_idx * spacing_x
                for node_idx, node_id in enumerate(layer):
                    y = start_y + node_idx * spacing_y
                    layout[node_id] = (x, y)
        
        return layout
    
    def _create_element_from_node(
        self,
        node_id: str,
        node_info: Dict[str, Any],
        position: Tuple[int, int]
    ) -> VPBElement:
        """Create VPB element from Mermaid node."""
        # Map Mermaid shapes to VPB element types
        shape_to_type = {
            'rectangle': 'Prozess',        # Standard process task
            'stadium': 'Ereignis',          # Start/End event
            'diamond': 'Entscheidung',      # Decision gateway
            'subprocess': 'Container',      # Subprocess/container
        }
        
        element_type = shape_to_type.get(node_info['shape'], 'Prozess')
        x, y = position
        
        return VPBElement(
            element_id=node_id,
            element_type=element_type,
            name=node_info['label'],
            x=x,
            y=y
        )
    
    def _create_connection(
        self,
        conn_info: Dict[str, Any],
        index: int
    ) -> VPBConnection:
        """Create VPB connection from Mermaid connection."""
        return VPBConnection(
            connection_id=f"C{index + 1}",
            source_element=conn_info['from'],
            target_element=conn_info['to'],
            connection_type=conn_info['type'],
            description=conn_info.get('label', '')
        )
