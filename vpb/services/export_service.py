"""
VPB Export Service
==================

Handles exporting process diagrams to various formats:
- PDF: High-quality print output using ReportLab
- SVG: Scalable vector graphics for web display
- PNG: Raster images for presentations
- BPMN 2.0: Standard XML format for interoperability
- Mermaid: Text-based diagrams for documentation and wikis
- Mermaid ERD: Entity-Relationship diagrams for database schemas

Author: VPB Development Team
Date: 2025-10-14
Updated: 2025-12-31 (Added Mermaid export and ERD support)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from xml.etree import ElementTree as ET
from io import BytesIO

from ..models.document import DocumentModel
from ..models.element import ELEMENT_TYPES
from ..models.connection import CONNECTION_TYPES, VPBConnection
from ..infrastructure.event_bus import EventBus


# ============================================================================
# Exception Classes
# ============================================================================

class ExportServiceError(Exception):
    """Base exception for export service errors."""
    pass


class PDFExportError(ExportServiceError):
    """Error during PDF export."""
    pass


class SVGExportError(ExportServiceError):
    """Error during SVG export."""
    pass


class PNGExportError(ExportServiceError):
    """Error during PNG export."""
    pass


class BPMNExportError(ExportServiceError):
    """Error during BPMN export."""
    pass


class MermaidExportError(ExportServiceError):
    """Error during Mermaid export."""
    pass


# ============================================================================
# Export Configuration
# ============================================================================

@dataclass
class ExportConfig:
    """Configuration for export operations."""
    
    # PDF settings
    pdf_page_size: str = 'A4'  # A4, Letter, Legal, A3
    pdf_orientation: str = 'portrait'  # portrait, landscape
    pdf_margin: int = 50  # pixels
    
    # SVG settings
    svg_width: int = 1200
    svg_height: int = 800
    svg_background: str = '#ffffff'
    
    # PNG settings
    png_width: int = 1920
    png_height: int = 1080
    png_dpi: int = 300
    png_background: str = '#ffffff'
    
    # BPMN settings
    bpmn_include_di: bool = True  # Include diagram interchange
    bpmn_namespace: str = 'http://www.omg.org/spec/BPMN/20100524/MODEL'
    
    # Mermaid settings
    mermaid_diagram_type: str = 'flowchart'  # flowchart, graph
    mermaid_direction: str = 'TB'  # TB (top-bottom), LR (left-right), BT, RL
    mermaid_include_metadata: bool = True
    mermaid_style_elements: bool = True  # Add styling to elements
    
    # General
    include_metadata: bool = True
    include_timestamp: bool = True


# ============================================================================
# Export Service
# ============================================================================

class ExportService:
    """
    Service for exporting process diagrams to various formats.
    
    Supports:
    - PDF export using ReportLab
    - SVG export with XML generation
    - PNG export using PIL/Pillow
    - BPMN 2.0 XML export for interoperability
    - Mermaid diagram export for documentation
    
    Example:
        >>> service = ExportService()
        >>> service.export_to_pdf(document, "output.pdf")
        >>> service.export_to_svg(document, "output.svg")
        >>> service.export_to_mermaid(document, "output.md")
    """
    
    def __init__(self, config: Optional[ExportConfig] = None):
        """
        Initialize the export service.
        
        Args:
            config: Export configuration (uses defaults if not provided)
        """
        self.config = config or ExportConfig()
        self.event_bus = EventBus()
    
    # ========================================================================
    # PDF Export
    # ========================================================================
    
    def export_to_pdf(
        self,
        document: DocumentModel,
        output_path: str,
        page_size: Optional[str] = None,
        orientation: Optional[str] = None
    ) -> Path:
        """
        Export process diagram to PDF format.
        
        Uses ReportLab to generate high-quality PDF output suitable for
        printing. Renders all elements and connections with proper styling.
        
        Args:
            document: The document to export
            output_path: Path to save PDF file
            page_size: Page size (A4, Letter, Legal, A3), None=use config
            orientation: portrait or landscape, None=use config
            
        Returns:
            Path to the created PDF file
            
        Raises:
            PDFExportError: If PDF export fails
            
        Example:
            >>> service.export_to_pdf(doc, "process.pdf", "A4", "landscape")
        """
        try:
            # Import ReportLab (lazy import to avoid dependency if not used)
            try:
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import A4, LETTER, LEGAL, A3, landscape
                from reportlab.lib import colors
            except ImportError as e:
                raise PDFExportError(
                    "ReportLab library not installed. "
                    "Install with: pip install reportlab"
                ) from e
            
            # Publish start event
            self.event_bus.publish('export:pdf:started', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': output_path
            })
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine page size
            page_size = page_size or self.config.pdf_page_size
            orientation_mode = orientation or self.config.pdf_orientation
            
            # Map page size strings to ReportLab sizes
            page_sizes = {
                'A4': A4,
                'LETTER': LETTER,
                'LEGAL': LEGAL,
                'A3': A3
            }
            
            size = page_sizes.get(page_size.upper(), A4)
            if orientation_mode.lower() == 'landscape':
                size = landscape(size)
            
            # Create PDF canvas
            pdf = canvas.Canvas(str(output_file), pagesize=size)
            page_width, page_height = size
            
            # Add metadata
            if self.config.include_metadata:
                pdf.setTitle(document.metadata.title or 'VPB Process Diagram')
                pdf.setAuthor(document.metadata.author or 'VPB Process Designer')
                pdf.setSubject(document.metadata.description or '')
                if self.config.include_timestamp:
                    pdf.setCreator(f'VPB Export Service - {datetime.now().isoformat()}')
            
            # Calculate bounds and scaling
            bounds = self._calculate_document_bounds(document)
            if bounds:
                min_x, min_y, max_x, max_y = bounds
                doc_width = max_x - min_x
                doc_height = max_y - min_y
                
                # Calculate scaling to fit page with margin
                margin = self.config.pdf_margin
                available_width = page_width - 2 * margin
                available_height = page_height - 2 * margin
                
                scale_x = available_width / doc_width if doc_width > 0 else 1
                scale_y = available_height / doc_height if doc_height > 0 else 1
                scale = min(scale_x, scale_y, 1.0)  # Don't scale up, only down
                
                # Center on page
                offset_x = margin + (available_width - doc_width * scale) / 2 - min_x * scale
                offset_y = margin + (available_height - doc_height * scale) / 2 - min_y * scale
            else:
                scale = 1.0
                offset_x = self.config.pdf_margin
                offset_y = self.config.pdf_margin
            
            # Render connections first (so they appear behind elements)
            for conn in document.get_all_connections():
                self._render_pdf_connection(pdf, conn, document, scale, offset_x, offset_y, page_height)
            
            # Render elements
            for element in document.get_all_elements():
                self._render_pdf_element(pdf, element, scale, offset_x, offset_y, page_height)
            
            # Add footer with metadata
            if self.config.include_timestamp:
                pdf.setFont("Helvetica", 8)
                pdf.setFillColor(colors.grey)
                footer_text = f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | VPB Process Designer"
                pdf.drawString(margin, 20, footer_text)
            
            # Save PDF
            pdf.save()
            
            # Publish success event
            self.event_bus.publish('export:pdf:completed', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': str(output_file)
            })
            
            return output_file
            
        except PDFExportError:
            raise
        except Exception as e:
            error_msg = f"PDF export failed: {str(e)}"
            self.event_bus.publish('export:pdf:error', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'error': error_msg
            })
            raise PDFExportError(error_msg) from e
    
    def _render_pdf_element(self, pdf, element, scale, offset_x, offset_y, page_height):
        """Render a single element to PDF canvas."""
        from reportlab.lib import colors
        
        # Get element bounds (handles missing width/height)
        elem_x, elem_y, elem_width, elem_height = self._get_element_bounds(element)
        
        # Transform coordinates (PDF Y-axis is bottom-up)
        x = elem_x * scale + offset_x
        y = page_height - (elem_y * scale + offset_y)
        width = elem_width * scale
        height = elem_height * scale
        
        # Set colors based on element type
        fill_color = self._get_element_color_for_type(element.element_type)
        pdf.setFillColor(fill_color)
        pdf.setStrokeColor(colors.black)
        pdf.setLineWidth(1)
        
        # Draw shape based on type
        if element.element_type in ['Prozess', 'VorProzess', 'NachProzess']:
            pdf.rect(x, y - height, width, height, fill=1, stroke=1)
        elif element.element_type == 'Entscheidung':
            # Diamond shape
            pdf.saveState()
            path = pdf.beginPath()
            path.moveTo(x + width/2, y)
            path.lineTo(x + width, y - height/2)
            path.lineTo(x + width/2, y - height)
            path.lineTo(x, y - height/2)
            path.close()
            pdf.drawPath(path, fill=1, stroke=1)
            pdf.restoreState()
        elif element.element_type == 'Ereignis':
            # Circle
            radius = min(width, height) / 2
            pdf.circle(x + width/2, y - height/2, radius, fill=1, stroke=1)
        else:
            # Default rectangle
            pdf.rect(x, y - height, width, height, fill=1, stroke=1)
        
        # Draw text
        if element.name:
            pdf.setFillColor(colors.black)
            pdf.setFont("Helvetica", max(8, int(10 * scale)))
            text_x = x + width / 2
            text_y = y - height / 2
            pdf.drawCentredString(text_x, text_y, element.name[:30])  # Limit length
    
    def _render_pdf_connection(self, pdf, connection, document, scale, offset_x, offset_y, page_height):
        """Render a connection to PDF canvas."""
        from reportlab.lib import colors
        
        # Get source and target elements
        source = next((e for e in document.get_all_elements() if e.element_id == connection.source_element), None)
        target = next((e for e in document.get_all_elements() if e.element_id == connection.target_element), None)
        
        if not source or not target:
            return
        
        # Get element bounds
        src_x, src_y, src_w, src_h = self._get_element_bounds(source)
        tgt_x, tgt_y, tgt_w, tgt_h = self._get_element_bounds(target)
        
        # Transform coordinates
        start_x = (src_x + src_w / 2) * scale + offset_x
        start_y = page_height - ((src_y + src_h / 2) * scale + offset_y)
        end_x = (tgt_x + tgt_w / 2) * scale + offset_x
        end_y = page_height - ((tgt_y + tgt_h / 2) * scale + offset_y)
        
        # Set style based on connection type
        pdf.setStrokeColor(colors.black)
        if connection.connection_type == 'SEQUENCE':
            pdf.setLineWidth(2)
            pdf.setDash([])
        elif connection.connection_type == 'INFORMATION':
            pdf.setLineWidth(1)
            pdf.setDash([5, 3])
        else:
            pdf.setLineWidth(1)
            pdf.setDash([])
        
        # Draw line
        pdf.line(start_x, start_y, end_x, end_y)
        
        # Draw arrow head
        self._draw_pdf_arrow(pdf, start_x, start_y, end_x, end_y)
    
    def _draw_pdf_arrow(self, pdf, x1, y1, x2, y2):
        """Draw arrow head at end of line."""
        import math
        
        # Calculate arrow head points
        arrow_length = 10
        arrow_angle = 0.5  # radians
        
        angle = math.atan2(y2 - y1, x2 - x1)
        
        # Arrow head points
        left_x = x2 - arrow_length * math.cos(angle - arrow_angle)
        left_y = y2 - arrow_length * math.sin(angle - arrow_angle)
        right_x = x2 - arrow_length * math.cos(angle + arrow_angle)
        right_y = y2 - arrow_length * math.sin(angle + arrow_angle)
        
        # Draw arrow head
        pdf.line(x2, y2, left_x, left_y)
        pdf.line(x2, y2, right_x, right_y)
    
    # ========================================================================
    # SVG Export
    # ========================================================================
    
    def export_to_svg(
        self,
        document: DocumentModel,
        output_path: str,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Path:
        """
        Export process diagram to SVG format.
        
        Generates scalable vector graphics suitable for web display and
        further editing in vector graphics tools.
        
        Args:
            document: The document to export
            output_path: Path to save SVG file
            width: SVG width in pixels, None=use config
            height: SVG height in pixels, None=use config
            
        Returns:
            Path to the created SVG file
            
        Raises:
            SVGExportError: If SVG export fails
        """
        try:
            self.event_bus.publish('export:svg:started', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': output_path
            })
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            width = width or self.config.svg_width
            height = height or self.config.svg_height
            
            # Calculate bounds
            bounds = self._calculate_document_bounds(document)
            if bounds:
                min_x, min_y, max_x, max_y = bounds
                viewBox = f"{min_x} {min_y} {max_x - min_x} {max_y - min_y}"
            else:
                viewBox = f"0 0 {width} {height}"
            
            # Create SVG root element
            svg = ET.Element('svg', {
                'xmlns': 'http://www.w3.org/2000/svg',
                'xmlns:xlink': 'http://www.w3.org/1999/xlink',
                'width': str(width),
                'height': str(height),
                'viewBox': viewBox
            })
            
            # Add metadata
            if self.config.include_metadata:
                metadata = ET.SubElement(svg, 'metadata')
                title = ET.SubElement(metadata, 'title')
                title.text = document.metadata.title or 'VPB Process Diagram'
                if self.config.include_timestamp:
                    desc = ET.SubElement(metadata, 'desc')
                    desc.text = f'Exported: {datetime.now().isoformat()} | VPB Process Designer'
            
            # Add background
            bg_rect = ET.SubElement(svg, 'rect', {
                'x': '0', 'y': '0',
                'width': '100%', 'height': '100%',
                'fill': self.config.svg_background
            })
            
            # Group for connections (drawn first)
            conn_group = ET.SubElement(svg, 'g', {'id': 'connections'})
            for conn in document.get_all_connections():
                self._render_svg_connection(conn_group, conn, document)
            
            # Group for elements
            elem_group = ET.SubElement(svg, 'g', {'id': 'elements'})
            for element in document.get_all_elements():
                self._render_svg_element(elem_group, element)
            
            # Write to file
            tree = ET.ElementTree(svg)
            ET.indent(tree, space='  ')
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            
            self.event_bus.publish('export:svg:completed', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': str(output_file)
            })
            
            return output_file
            
        except SVGExportError:
            raise
        except Exception as e:
            error_msg = f"SVG export failed: {str(e)}"
            self.event_bus.publish('export:svg:error', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'error': error_msg
            })
            raise SVGExportError(error_msg) from e
    
    def _render_svg_element(self, parent, element):
        """Render a single element to SVG."""
        group = ET.SubElement(parent, 'g', {'id': f'element-{element.element_id}'})
        
        fill_color = self._get_element_color_hex(element.element_type)
        
        # Get element bounds
        elem_x, elem_y, elem_width, elem_height = self._get_element_bounds(element)
        
        # Draw shape based on type
        if element.element_type in ['Prozess', 'VorProzess', 'NachProzess', 'Container']:
            ET.SubElement(group, 'rect', {
                'x': str(elem_x),
                'y': str(elem_y),
                'width': str(elem_width),
                'height': str(elem_height),
                'fill': fill_color,
                'stroke': '#000000',
                'stroke-width': '2'
            })
        elif element.element_type == 'Entscheidung':
            # Diamond
            cx = elem_x + elem_width / 2
            cy = elem_y + elem_height / 2
            points = [
                (cx, elem_y),
                (elem_x + elem_width, cy),
                (cx, elem_y + elem_height),
                (elem_x, cy)
            ]
            points_str = ' '.join([f"{x},{y}" for x, y in points])
            ET.SubElement(group, 'polygon', {
                'points': points_str,
                'fill': fill_color,
                'stroke': '#000000',
                'stroke-width': '2'
            })
        elif element.element_type == 'Ereignis':
            # Circle
            cx = elem_x + elem_width / 2
            cy = elem_y + elem_height / 2
            r = min(elem_width, elem_height) / 2
            ET.SubElement(group, 'circle', {
                'cx': str(cx),
                'cy': str(cy),
                'r': str(r),
                'fill': fill_color,
                'stroke': '#000000',
                'stroke-width': '2'
            })
        else:
            # Default rectangle
            ET.SubElement(group, 'rect', {
                'x': str(elem_x),
                'y': str(elem_y),
                'width': str(elem_width),
                'height': str(elem_height),
                'fill': fill_color,
                'stroke': '#000000',
                'stroke-width': '2'
            })
        
        # Add text
        if element.name:
            text_x = elem_x + elem_width / 2
            text_y = elem_y + elem_height / 2
            text = ET.SubElement(group, 'text', {
                'x': str(text_x),
                'y': str(text_y),
                'text-anchor': 'middle',
                'dominant-baseline': 'middle',
                'font-family': 'Arial, sans-serif',
                'font-size': '12',
                'fill': '#000000'
            })
            text.text = element.name
    
    def _render_svg_connection(self, parent, connection, document):
        """Render a connection to SVG."""
        source = next((e for e in document.get_all_elements() if e.element_id == connection.source_element), None)
        target = next((e for e in document.get_all_elements() if e.element_id == connection.target_element), None)
        
        if not source or not target:
            return
        
        # Get element bounds
        src_x, src_y, src_w, src_h = self._get_element_bounds(source)
        tgt_x, tgt_y, tgt_w, tgt_h = self._get_element_bounds(target)
        
        # Calculate connection points
        start_x = src_x + src_w / 2
        start_y = src_y + src_h / 2
        end_x = tgt_x + tgt_w / 2
        end_y = tgt_y + tgt_h / 2
        
        # Line style
        stroke_dasharray = '5,3' if connection.connection_type == 'INFORMATION' else 'none'
        
        # Draw line
        ET.SubElement(parent, 'line', {
            'x1': str(start_x),
            'y1': str(start_y),
            'x2': str(end_x),
            'y2': str(end_y),
            'stroke': '#000000',
            'stroke-width': '2',
            'stroke-dasharray': stroke_dasharray,
            'marker-end': 'url(#arrowhead)'
        })
        
        # Ensure arrowhead marker is defined (add once to SVG root)
        if not parent.find('.//marker[@id="arrowhead"]'):
            defs = parent.find('.//defs')
            if defs is None:
                defs = ET.SubElement(parent, 'defs')
            
            marker = ET.SubElement(defs, 'marker', {
                'id': 'arrowhead',
                'markerWidth': '10',
                'markerHeight': '10',
                'refX': '9',
                'refY': '3',
                'orient': 'auto'
            })
            ET.SubElement(marker, 'polygon', {
                'points': '0 0, 10 3, 0 6',
                'fill': '#000000'
            })
    
    # ========================================================================
    # PNG Export
    # ========================================================================
    
    def export_to_png(
        self,
        document: DocumentModel,
        output_path: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        dpi: Optional[int] = None
    ) -> Path:
        """
        Export process diagram to PNG format.
        
        Generates raster image suitable for presentations and documents.
        Uses PIL/Pillow for rendering.
        
        Args:
            document: The document to export
            output_path: Path to save PNG file
            width: Image width in pixels, None=use config
            height: Image height in pixels, None=use config
            dpi: Image resolution, None=use config
            
        Returns:
            Path to the created PNG file
            
        Raises:
            PNGExportError: If PNG export fails
        """
        try:
            # Import PIL (lazy import)
            try:
                from PIL import Image, ImageDraw, ImageFont
            except ImportError as e:
                raise PNGExportError(
                    "PIL/Pillow library not installed. "
                    "Install with: pip install Pillow"
                ) from e
            
            self.event_bus.publish('export:png:started', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': output_path
            })
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            width = width or self.config.png_width
            height = height or self.config.png_height
            dpi = dpi or self.config.png_dpi
            
            # Create image
            img = Image.new('RGB', (width, height), self.config.png_background)
            draw = ImageDraw.Draw(img)
            
            # Calculate bounds and scaling
            bounds = self._calculate_document_bounds(document)
            if bounds:
                min_x, min_y, max_x, max_y = bounds
                doc_width = max_x - min_x
                doc_height = max_y - min_y
                
                margin = 50
                scale_x = (width - 2 * margin) / doc_width if doc_width > 0 else 1
                scale_y = (height - 2 * margin) / doc_height if doc_height > 0 else 1
                scale = min(scale_x, scale_y, 1.0)
                
                offset_x = margin + ((width - 2 * margin) - doc_width * scale) / 2 - min_x * scale
                offset_y = margin + ((height - 2 * margin) - doc_height * scale) / 2 - min_y * scale
            else:
                scale = 1.0
                offset_x = 50
                offset_y = 50
            
            # Load font
            try:
                font = ImageFont.truetype("arial.ttf", int(12 * scale))
            except:
                font = ImageFont.load_default()
            
            # Render connections
            for conn in document.get_all_connections():
                self._render_png_connection(draw, conn, document, scale, offset_x, offset_y)
            
            # Render elements
            for element in document.get_all_elements():
                self._render_png_element(draw, element, scale, offset_x, offset_y, font)
            
            # Save with metadata
            img.save(output_file, dpi=(dpi, dpi))
            
            self.event_bus.publish('export:png:completed', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': str(output_file)
            })
            
            return output_file
            
        except PNGExportError:
            raise
        except Exception as e:
            error_msg = f"PNG export failed: {str(e)}"
            self.event_bus.publish('export:png:error', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'error': error_msg
            })
            raise PNGExportError(error_msg) from e
    
    def _render_png_element(self, draw, element, scale, offset_x, offset_y, font):
        """Render element to PNG using PIL."""
        # Get element bounds
        elem_x, elem_y, elem_width, elem_height = self._get_element_bounds(element)
        
        x = elem_x * scale + offset_x
        y = elem_y * scale + offset_y
        width = elem_width * scale
        height = elem_height * scale
        
        fill_color = self._get_element_color_hex(element.element_type)
        outline_color = '#000000'
        
        # Draw shape
        if element.element_type in ['Prozess', 'VorProzess', 'NachProzess', 'Container']:
            draw.rectangle([x, y, x + width, y + height], fill=fill_color, outline=outline_color, width=2)
        elif element.element_type == 'Entscheidung':
            # Diamond
            cx = x + width / 2
            cy = y + height / 2
            points = [(cx, y), (x + width, cy), (cx, y + height), (x, cy)]
            draw.polygon(points, fill=fill_color, outline=outline_color)
        elif element.element_type == 'Ereignis':
            # Circle
            r = min(width, height) / 2
            cx = x + width / 2
            cy = y + height / 2
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill_color, outline=outline_color, width=2)
        else:
            draw.rectangle([x, y, x + width, y + height], fill=fill_color, outline=outline_color, width=2)
        
        # Draw text
        if element.name:
            text_bbox = draw.textbbox((0, 0), element.name, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x + (width - text_width) / 2
            text_y = y + (height - text_height) / 2
            draw.text((text_x, text_y), element.name, fill='#000000', font=font)
    
    def _render_png_connection(self, draw, connection, document, scale, offset_x, offset_y):
        """Render connection to PNG using PIL."""
        source = next((e for e in document.get_all_elements() if e.element_id == connection.source_element), None)
        target = next((e for e in document.get_all_elements() if e.element_id == connection.target_element), None)
        
        if not source or not target:
            return
        
        # Get element bounds
        src_x, src_y, src_w, src_h = self._get_element_bounds(source)
        tgt_x, tgt_y, tgt_w, tgt_h = self._get_element_bounds(target)
        
        start_x = (src_x + src_w / 2) * scale + offset_x
        start_y = (src_y + src_h / 2) * scale + offset_y
        end_x = (tgt_x + tgt_w / 2) * scale + offset_x
        end_y = (tgt_y + tgt_h / 2) * scale + offset_y
        
        # Draw line
        draw.line([start_x, start_y, end_x, end_y], fill='#000000', width=2)
        
        # Draw arrow head
        import math
        arrow_length = 10
        angle = math.atan2(end_y - start_y, end_x - start_x)
        left_x = end_x - arrow_length * math.cos(angle - 0.5)
        left_y = end_y - arrow_length * math.sin(angle - 0.5)
        right_x = end_x - arrow_length * math.cos(angle + 0.5)
        right_y = end_y - arrow_length * math.sin(angle + 0.5)
        draw.polygon([(end_x, end_y), (left_x, left_y), (right_x, right_y)], fill='#000000')
    
    # ========================================================================
    # Mermaid Export
    # ========================================================================
    
    def export_to_mermaid(
        self,
        document: DocumentModel,
        output_path: str,
        diagram_type: Optional[str] = None,
        direction: Optional[str] = None
    ) -> Path:
        """
        Export process diagram to Mermaid format.
        
        Mermaid is a JavaScript-based diagramming tool that uses text-based
        syntax to create diagrams. This export creates Mermaid flowchart syntax
        that can be rendered in documentation, wikis, or using mermaid-cli.
        
        Supports diagram types:
        - flowchart/graph: Process flow diagrams
        - erDiagram: Entity-Relationship diagrams for database schemas
        
        Args:
            document: The document to export
            output_path: Path to save Mermaid file (.md or .mmd)
            diagram_type: Type of diagram (flowchart, graph, erDiagram), None=use config
            direction: Flow direction (TB, LR, BT, RL), None=use config (not used for ERD)
            
        Returns:
            Path to the created Mermaid file
            
        Raises:
            MermaidExportError: If Mermaid export fails
            
        Example:
            >>> service.export_to_mermaid(doc, "process.md", "flowchart", "LR")
            >>> service.export_to_mermaid(doc, "schema.md", "erDiagram")
        """
        try:
            # Publish start event
            self.event_bus.publish('export:mermaid:started', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': output_path
            })
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine diagram type and direction
            diagram_type = diagram_type or self.config.mermaid_diagram_type
            direction = direction or self.config.mermaid_direction
            
            # Generate Mermaid content based on diagram type
            if diagram_type == 'erDiagram':
                mermaid_content = self._generate_mermaid_erd(document)
            else:
                mermaid_content = self._generate_mermaid_diagram(
                    document, diagram_type, direction
                )
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(mermaid_content)
            
            # Publish success event
            self.event_bus.publish('export:mermaid:completed', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': str(output_file)
            })
            
            return output_file
            
        except Exception as e:
            # Publish error event
            self.event_bus.publish('export:mermaid:failed', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'error': str(e)
            })
            raise MermaidExportError(f"Failed to export Mermaid: {e}") from e
    
    def _generate_mermaid_diagram(
        self,
        document: DocumentModel,
        diagram_type: str,
        direction: str
    ) -> str:
        """
        Generate Mermaid diagram syntax from document.
        
        Args:
            document: Document to convert
            diagram_type: Type of Mermaid diagram
            direction: Flow direction
            
        Returns:
            Mermaid diagram as string
        """
        lines = []
        
        # Add metadata as comments if enabled
        if self.config.mermaid_include_metadata:
            lines.append("---")
            lines.append(f"title: {document.metadata.title or 'VPB Process Diagram'}")
            if document.metadata.description:
                lines.append(f"description: {document.metadata.description}")
            if document.metadata.author:
                lines.append(f"author: {document.metadata.author}")
            if self.config.include_timestamp:
                lines.append(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("---")
            lines.append("")
        
        # Start diagram definition
        lines.append(f"{diagram_type} {direction}")
        lines.append("")
        
        # Map element IDs to Mermaid-compatible IDs
        element_map = {}
        for i, element in enumerate(document.get_all_elements()):
            # Create safe ID (alphanumeric only)
            safe_id = f"node{i}"
            element_map[element.element_id] = safe_id
            
            # Determine node shape based on element type
            shape = self._get_mermaid_shape(element.element_type)
            label = element.name or element.element_type
            
            # Add node definition with shape
            lines.append(f"    {safe_id}{shape[0]}\"{label}\"{shape[1]}")
        
        lines.append("")
        
        # Add connections
        for connection in document.get_all_connections():
            source_id = element_map.get(connection.source_element)
            target_id = element_map.get(connection.target_element)
            
            if source_id and target_id:
                # Determine arrow style
                arrow = self._get_mermaid_arrow(connection.connection_type)
                
                # Add label if available
                if hasattr(connection, 'label') and connection.label:
                    lines.append(f"    {source_id} {arrow}|\"{connection.label}\"| {target_id}")
                else:
                    lines.append(f"    {source_id} {arrow} {target_id}")
        
        # Add styling if enabled
        if self.config.mermaid_style_elements:
            lines.append("")
            lines.append("    %% Styling")
            for i, element in enumerate(document.get_all_elements()):
                safe_id = f"node{i}"
                style = self._get_mermaid_style(element.element_type)
                if style:
                    lines.append(f"    style {safe_id} {style}")
        
        return "\n".join(lines)
    
    def _get_mermaid_shape(self, element_type: str) -> Tuple[str, str]:
        """
        Get Mermaid shape brackets for element type.
        
        Returns tuple of (opening, closing) brackets.
        """
        shape_map = {
            'Ereignis': ('[', ']'),  # Rectangle (event)
            'Prozess': ('[', ']'),  # Rectangle (process)
            'VorProzess': ('[', ']'),  # Rectangle
            'NachProzess': ('[', ']'),  # Rectangle
            'Entscheidung': ('{', '}'),  # Diamond (decision)
            'XOR': ('{', '}'),  # Diamond
            'OR': ('{', '}'),  # Diamond
            'AND': ('{', '}'),  # Diamond
            'Container': ('[[', ']]'),  # Subprocess
            'START': ('([', '])'),  # Stadium (rounded)
            'END': ('([', '])'),  # Stadium (rounded)
        }
        return shape_map.get(element_type, ('[', ']'))  # Default rectangle
    
    def _get_mermaid_arrow(self, connection_type: str) -> str:
        """Get Mermaid arrow style for connection type."""
        arrow_map = {
            'sequence': '-->',  # Solid arrow
            'conditional': '-.->',  # Dotted arrow
            'default': '-->',
        }
        return arrow_map.get(connection_type, '-->')
    
    def _get_mermaid_style(self, element_type: str) -> str:
        """Get Mermaid CSS style for element type."""
        color = self._get_element_color_hex(element_type)
        # Convert hex to fill and stroke styles
        return f"fill:{color},stroke:#333,stroke-width:2px"
    
    def _generate_mermaid_erd(self, document: DocumentModel) -> str:
        """
        Generate Mermaid Entity-Relationship Diagram from document.
        
        Interprets VPB elements as database entities and connections as relationships.
        Useful for modeling database schemas and queries.
        
        Args:
            document: Document to convert
            
        Returns:
            Mermaid ERD diagram as string
        """
        lines = []
        
        # Add metadata if enabled
        if self.config.mermaid_include_metadata:
            lines.append("---")
            lines.append(f"title: {document.metadata.title or 'Database Schema'}")
            if document.metadata.description:
                lines.append(f"description: {document.metadata.description}")
            if document.metadata.author:
                lines.append(f"author: {document.metadata.author}")
            if self.config.include_timestamp:
                lines.append(f"created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("---")
            lines.append("")
        
        lines.append("erDiagram")
        lines.append("")
        
        # Map elements to entities
        entities = {}
        for element in document.get_all_elements():
            # Use element name as entity name (sanitize for Mermaid)
            entity_name = (element.name or element.element_id).replace(' ', '_').replace('-', '_')
            entities[element.element_id] = entity_name
            
            # Add entity with attributes if description contains field definitions
            lines.append(f"    {entity_name} {{")
            
            # Parse description for attributes (format: "field_name type")
            description = getattr(element, 'description', '')
            if description:
                # Split by newlines or semicolons
                attrs = [a.strip() for a in description.replace(';', '\n').split('\n') if a.strip()]
                for attr in attrs:
                    # Expected format: "field_name type" or just "field_name"
                    parts = attr.split()
                    if len(parts) >= 2:
                        field_name = parts[0]
                        field_type = ' '.join(parts[1:])
                        lines.append(f"        {field_type} {field_name}")
                    elif len(parts) == 1:
                        lines.append(f"        string {parts[0]}")
            
            # If no attributes specified, add a default ID field
            if not description or (';' not in description and '\n' not in description):
                lines.append(f"        int id PK")
                lines.append(f"        string name")
            
            lines.append("    }")
            lines.append("")
        
        # Add relationships
        for connection in document.get_all_connections():
            source_entity = entities.get(connection.source_element)
            target_entity = entities.get(connection.target_element)
            
            if source_entity and target_entity:
                # Determine relationship cardinality from connection type or description
                # Default: one-to-many
                relationship = self._get_erd_relationship(connection)
                label = getattr(connection, 'description', '') or getattr(connection, 'label', '')
                
                if label:
                    # Sanitize label for Mermaid
                    label = label.replace('"', "'")
                    lines.append(f'    {source_entity} {relationship} {target_entity} : "{label}"')
                else:
                    lines.append(f'    {source_entity} {relationship} {target_entity} : "has"')
        
        return "\n".join(lines)
    
    def _get_erd_relationship(self, connection: VPBConnection) -> str:
        """
        Determine ERD relationship cardinality from connection.
        
        Returns Mermaid ERD relationship syntax.
        
        Cardinality can be specified in connection description:
        - "1:1" or "one-to-one" -> ||--||
        - "1:N" or "one-to-many" -> ||--o{
        - "N:M" or "many-to-many" -> }o--o{
        - "0:1" or "zero-or-one" -> ||--o|
        """
        desc = (getattr(connection, 'description', '') or '').lower()
        conn_type = (getattr(connection, 'connection_type', '') or '').lower()
        
        # Check for explicit cardinality in description
        if '1:1' in desc or 'one-to-one' in desc or 'onetoone' in desc:
            return '||--||'
        elif 'n:m' in desc or 'many-to-many' in desc or 'manytomany' in desc or 'm:n' in desc:
            return '}o--o{'
        elif '1:n' in desc or 'one-to-many' in desc or 'onetomany' in desc:
            return '||--o{'
        elif '0:1' in desc or 'zero-or-one' in desc or 'optional' in desc:
            return '||--o|'
        elif 'n:1' in desc or 'many-to-one' in desc or 'manytoone' in desc:
            return '}o--||'
        
        # Default: one-to-many (most common in databases)
        return '||--o{'
    
    # ========================================================================
    # BPMN 2.0 XML Export
    # ========================================================================
    
    def export_to_bpmn(
        self,
        document: DocumentModel,
        output_path: str,
        include_di: Optional[bool] = None
    ) -> Path:
        """
        Export process diagram to BPMN 2.0 XML format.
        
        Generates standard BPMN 2.0 XML for interoperability with other
        BPMN tools like Camunda, Activiti, or other process engines.
        
        Args:
            document: The document to export
            output_path: Path to save BPMN XML file
            include_di: Include diagram interchange, None=use config
            
        Returns:
            Path to the created BPMN file
            
        Raises:
            BPMNExportError: If BPMN export fails
        """
        try:
            self.event_bus.publish('export:bpmn:started', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': output_path
            })
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            include_di = include_di if include_di is not None else self.config.bpmn_include_di
            
            # BPMN namespaces
            ns_bpmn = self.config.bpmn_namespace
            ns_bpmndi = 'http://www.omg.org/spec/BPMN/20100524/DI'
            ns_dc = 'http://www.omg.org/spec/DD/20100524/DC'
            ns_di = 'http://www.omg.org/spec/DD/20100524/DI'
            
            # Register namespaces
            ET.register_namespace('bpmn', ns_bpmn)
            ET.register_namespace('bpmndi', ns_bpmndi)
            ET.register_namespace('dc', ns_dc)
            ET.register_namespace('di', ns_di)
            
            # Create root definitions element
            definitions = ET.Element(f'{{{ns_bpmn}}}definitions', {
                'id': f'Definitions_{getattr(document, "document_id", str(id(document)))}',
                'targetNamespace': 'http://bpmn.io/schema/bpmn',
                'exporter': 'VPB Process Designer',
                'exporterVersion': '1.0'
            })
            
            # Create process element
            process = ET.SubElement(definitions, f'{{{ns_bpmn}}}process', {
                'id': f'Process_{getattr(document, "document_id", str(id(document)))}',
                'isExecutable': 'false'
            })
            
            # Add process name
            if document.metadata.title:
                process.set('name', document.metadata.title)
            
            # Map VPB elements to BPMN elements
            for element in document.get_all_elements():
                self._create_bpmn_element(process, element, ns_bpmn)
            
            # Map VPB connections to BPMN sequence flows
            for connection in document.get_all_connections():
                self._create_bpmn_sequence_flow(process, connection, ns_bpmn)
            
            # Add diagram interchange if requested
            if include_di:
                self._add_bpmn_diagram_interchange(definitions, document, ns_bpmndi, ns_dc, ns_di)
            
            # Write to file
            tree = ET.ElementTree(definitions)
            ET.indent(tree, space='  ')
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            
            self.event_bus.publish('export:bpmn:completed', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'output_path': str(output_file)
            })
            
            return output_file
            
        except BPMNExportError:
            raise
        except Exception as e:
            error_msg = f"BPMN export failed: {str(e)}"
            self.event_bus.publish('export:bpmn:error', {
                'document_id': getattr(document, "document_id", str(id(document))),
                'error': error_msg
            })
            raise BPMNExportError(error_msg) from e
    
    def _create_bpmn_element(self, process, element, ns_bpmn):
        """Create BPMN element from VPB element."""
        element_map = {
            'Ereignis': 'startEvent',
            'Prozess': 'task',
            'VorProzess': 'task',
            'NachProzess': 'task',
            'Container': 'subProcess',
            'Entscheidung': 'exclusiveGateway',
            'AND': 'parallelGateway',
            'OR': 'inclusiveGateway',
            'XOR': 'exclusiveGateway',
        }
        
        bpmn_type = element_map.get(element.element_type, 'task')
        
        attrs = {
            'id': element.element_id,
        }
        if element.name:
            attrs['name'] = element.name
        
        ET.SubElement(process, f'{{{ns_bpmn}}}{bpmn_type}', attrs)
    
    def _create_bpmn_sequence_flow(self, process, connection, ns_bpmn):
        """Create BPMN sequence flow from VPB connection."""
        attrs = {
            'id': connection.connection_id,
            'sourceRef': connection.source_element,
            'targetRef': connection.target_element
        }
        if connection.description:
            attrs['name'] = connection.description
        
        ET.SubElement(process, f'{{{ns_bpmn}}}sequenceFlow', attrs)
    
    def _add_bpmn_diagram_interchange(self, definitions, document, ns_bpmndi, ns_dc, ns_di):
        """Add BPMN diagram interchange for visual information."""
        diagram = ET.SubElement(definitions, f'{{{ns_bpmndi}}}BPMNDiagram', {
            'id': f'Diagram_{getattr(document, "document_id", str(id(document)))}'
        })
        
        plane = ET.SubElement(diagram, f'{{{ns_bpmndi}}}BPMNPlane', {
            'id': f'Plane_{getattr(document, "document_id", str(id(document)))}',
            'bpmnElement': f'Process_{getattr(document, "document_id", str(id(document)))}'
        })
        
        # Add shapes for elements
        for element in document.get_all_elements():
            # Get element bounds
            elem_x, elem_y, elem_width, elem_height = self._get_element_bounds(element)
            
            shape = ET.SubElement(plane, f'{{{ns_bpmndi}}}BPMNShape', {
                'id': f'Shape_{element.element_id}',
                'bpmnElement': element.element_id
            })
            bounds = ET.SubElement(shape, f'{{{ns_dc}}}Bounds', {
                'x': str(elem_x),
                'y': str(elem_y),
                'width': str(elem_width),
                'height': str(elem_height)
            })
        
        # Add edges for connections
        for connection in document.get_all_connections():
            edge = ET.SubElement(plane, f'{{{ns_bpmndi}}}BPMNEdge', {
                'id': f'Edge_{connection.connection_id}',
                'bpmnElement': connection.connection_id
            })
            
            # Get source and target positions
            source = next((e for e in document.get_all_elements() if e.element_id == connection.source_element), None)
            target = next((e for e in document.get_all_elements() if e.element_id == connection.target_element), None)
            
            if source and target:
                # Get element bounds
                src_x, src_y, src_w, src_h = self._get_element_bounds(source)
                tgt_x, tgt_y, tgt_w, tgt_h = self._get_element_bounds(target)
                
                # Start waypoint
                ET.SubElement(edge, f'{{{ns_di}}}waypoint', {
                    'x': str(src_x + src_w / 2),
                    'y': str(src_y + src_h / 2)
                })
                # End waypoint
                ET.SubElement(edge, f'{{{ns_di}}}waypoint', {
                    'x': str(tgt_x + tgt_w / 2),
                    'y': str(tgt_y + tgt_h / 2)
                })
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _get_element_bounds(self, element):
        """Get element bounds with defaults for elements without width/height."""
        # Default sizes for VPB elements
        default_sizes = {
            'Ereignis': (60, 60),
            'Prozess': (120, 80),
            'VorProzess': (120, 80),
            'NachProzess': (120, 80),
            'Container': (150, 100),
            'Entscheidung': (80, 80),
            'AND': (80, 80),
            'OR': (80, 80),
            'XOR': (80, 80),
        }
        
        width = getattr(element, 'width', None)
        height = getattr(element, 'height', None)
        
        if width is None or height is None:
            width, height = default_sizes.get(element.element_type, (100, 80))
        
        return element.x, element.y, width, height
    
    def _calculate_document_bounds(self, document: DocumentModel) -> Optional[Tuple[float, float, float, float]]:
        """
        Calculate bounding box of all elements in document.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) or None if no elements
        """
        if not document.get_all_elements():
            return None
        
        bounds_list = []
        for e in document.get_all_elements():
            x, y, width, height = self._get_element_bounds(e)
            bounds_list.append((x, y, x + width, y + height))
        
        min_x = min(b[0] for b in bounds_list)
        min_y = min(b[1] for b in bounds_list)
        max_x = max(b[2] for b in bounds_list)
        max_y = max(b[3] for b in bounds_list)
        
        return (min_x, min_y, max_x, max_y)
    
    def _get_element_color_for_type(self, element_type: str):
        """Get ReportLab color for element type."""
        from reportlab.lib import colors
        
        color_map = {
            'Ereignis': colors.lightgreen,
            'Prozess': colors.lightblue,
            'VorProzess': colors.lightcyan,
            'NachProzess': colors.lightcyan,
            'Container': colors.lightyellow,
            'Entscheidung': colors.wheat,
            'AND': colors.wheat,
            'OR': colors.wheat,
            'XOR': colors.wheat,
        }
        return color_map.get(element_type, colors.lightgrey)
    
    def _get_element_color_hex(self, element_type: str) -> str:
        """Get hex color for element type."""
        color_map = {
            'Ereignis': '#90EE90',
            'Prozess': '#ADD8E6',
            'VorProzess': '#E0FFFF',
            'NachProzess': '#E0FFFF',
            'Container': '#FFFFE0',
            'Entscheidung': '#F5DEB3',
            'AND': '#F5DEB3',
            'OR': '#F5DEB3',
            'XOR': '#F5DEB3',
        }
        return color_map.get(element_type, '#D3D3D3')
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ExportService(config={self.config})"
