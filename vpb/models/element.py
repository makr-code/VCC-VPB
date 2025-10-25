"""
VPB Element Model
=================

Domain model for VPB process elements.

This module defines the VPBElement class representing individual process elements
like VorProzess, Prozess, NachProzess, Entscheidung, etc.

Features:
- Immutable data structure (frozen dataclass)
- Type validation
- Serialization (to_dict/from_dict)
- Geometry calculations
- Factory pattern for creation
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict, Any
from uuid import uuid4
import logging


logger = logging.getLogger(__name__)


@dataclass
class ConditionCheck:
    """
    Single condition check for CONDITION elements.
    
    Represents one condition to evaluate (e.g., "status == 'approved'").
    Multiple checks can be combined with AND/OR logic.
    
    Attributes:
        field: Field/variable name to check (e.g., "status", "amount", "date")
        operator: Comparison operator (==, !=, <, >, <=, >=, contains, regex)
        value: Value to compare against (string representation)
        check_type: Data type for comparison (string, number, date, boolean)
    """
    field: str
    operator: str
    value: str
    check_type: str = "string"  # string, number, date, boolean
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "check_type": self.check_type
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ConditionCheck':
        """Create ConditionCheck from dictionary."""
        return ConditionCheck(
            field=data.get("field") or "",
            operator=data.get("operator") or "==",
            value=data.get("value") or "",
            check_type=data.get("check_type") or "string"
        )


# Element type constants (Domain + UI Styles)
# Enthält sowohl deutschsprachige Domänenwerte als auch die im UI/Styles genutzten Typ-Keys
ELEMENT_TYPES = {
    # Deutschsprachige Typen (Domänenmodell)
    'VorProzess': 'Vor-Prozess',
    'Prozess': 'Prozess',
    'NachProzess': 'Nach-Prozess',
    'Entscheidung': 'Entscheidung',
    'Datenobjekt': 'Datenobjekt',
    'Ereignis': 'Ereignis',
    'Schnittstelle': 'Schnittstelle',
    'Container': 'Container',
    'AND': 'AND-Gateway',
    'OR': 'OR-Gateway',
    'XOR': 'XOR-Gateway',
    # UI/Styles kompatible Typen
    'FUNCTION': 'Funktion',
    'START_EVENT': 'Start-Ereignis',
    'END_EVENT': 'End-Ereignis',
    'EVENT': 'Ereignis',
    'GATEWAY': 'Gateway',
    'XOR_CONNECTOR': 'XOR-Gateway',
    'AND_CONNECTOR': 'AND-Gateway',
    'OR_CONNECTOR': 'OR-Gateway',
    'INFORMATION_OBJECT': 'Informationsobjekt',
    'ORGANIZATION_UNIT': 'Organisationseinheit',
    'DEADLINE': 'Frist',
    'LEGAL_CHECKPOINT': 'Rechtsprüfung',
    'COMPETENCY_CHECK': 'Kompetenzprüfung',
    'GEO_CONTEXT': 'Geo-Kontext',
    'SUBPROCESS': 'Teilprozess (Referenz)',
    'GROUP': 'Gruppe',
    # Zeit-Elemente (NEU)
    'TIME_LOOP': 'Zeitschleife',
    'TIMER': 'Timer/Zeitgeber',
    # SPS-Logik-Elemente (NEU)
    'COUNTER': 'Zähler (Counter)',
    'CONDITION': 'Bedingung (Condition)',
    'ERROR_HANDLER': 'Fehlerbehandlung (Error Handler)',
    'STATE': 'Zustand (State)',
    'INTERLOCK': 'Sperre (Interlock)',
}


@dataclass
class VPBElement:
    """
    VPB Process Element.
    
    Represents a single element in a VPB process diagram.
    
    Attributes:
        element_id: Unique identifier
        element_type: Type of element (VorProzess, Prozess, etc.)
        name: Display name/label
        x: X-coordinate on canvas
        y: Y-coordinate on canvas
        description: Detailed description
        responsible_authority: Responsible authority/department
        legal_basis: Legal basis reference
        deadline_days: Deadline in days
        geo_reference: Geographic reference
        ref_file: Reference to external file
        ref_inline_content: Inline content reference
        ref_inline_path: Path to inline content
        ref_inline_error: Error loading inline content
        ref_inline_truncated: Whether inline content was truncated
        ref_source_mtime: Modification time of source file
        original_element_type: Original type before transformation
        members: List of member element IDs (for containers)
        collapsed: Whether container is collapsed
        loop_type: Type of time loop (none, interval, cron, date, relative)
        loop_interval_minutes: Interval in minutes between repetitions
        loop_cron: Cron expression for scheduling
        loop_date: ISO date for one-time execution
        loop_relative_days: Days relative to process start
        loop_max_iterations: Maximum iterations (0 = unlimited)
        canvas_items: List of canvas item IDs
    """
    
    # Core properties
    element_id: str
    element_type: str
    name: str
    x: int
    y: int
    
    # Optional properties with defaults
    description: str = ""
    responsible_authority: str = ""
    legal_basis: str = ""
    deadline_days: int = 0
    geo_reference: str = ""
    
    # File references
    ref_file: str = ""
    ref_inline_content: Optional[str] = None
    ref_inline_path: Optional[str] = None
    ref_inline_error: Optional[str] = None
    ref_inline_truncated: bool = False
    ref_source_mtime: Optional[float] = None
    
    # Type transformation
    original_element_type: Optional[str] = None
    
    # Container properties
    members: List[str] = field(default_factory=list)
    collapsed: bool = False
    
    # Zeit-Properties (NEU für TIME_LOOP und TIMER)
    loop_type: str = "none"  # none, interval, cron, date, relative
    loop_interval_minutes: int = 0  # Für interval: Minuten zwischen Wiederholungen
    loop_cron: str = ""  # Für cron: Cron-Expression (z.B. "0 9 * * *" = täglich 9 Uhr)
    loop_date: str = ""  # Für date: ISO-Datum (z.B. "2025-12-31")
    loop_relative_days: int = 0  # Für relative: Tage relativ zu Prozessstart
    loop_max_iterations: int = 0  # 0 = unbegrenzt, >0 = max. Wiederholungen
    
    # Counter-Properties (NEU für COUNTER)
    counter_type: str = "UP"  # UP, DOWN, UP_DOWN
    counter_start_value: int = 0  # Startwert
    counter_max_value: int = 100  # Maximalwert
    counter_current_value: int = 0  # Aktueller Wert (Laufzeit)
    counter_reset_on_max: bool = False  # Bei Max zurücksetzen?
    counter_on_max_reached: str = ""  # Element-ID für Eskalation bei Maximum
    
    # Condition-Properties (NEU für CONDITION)
    condition_checks: List[Dict[str, Any]] = field(default_factory=list)  # Liste von ConditionCheck-Dicts
    condition_logic: str = "AND"  # AND, OR
    condition_true_target: str = ""  # Element-ID für TRUE-Fall
    condition_false_target: str = ""  # Element-ID für FALSE-Fall
    
    # Error-Handler-Properties (NEU für ERROR_HANDLER)
    error_handler_type: str = "RETRY"  # RETRY, FALLBACK, NOTIFY, ABORT
    error_handler_retry_count: int = 3  # Anzahl Wiederholungsversuche
    error_handler_retry_delay: int = 60  # Verzögerung zwischen Retries (Sekunden)
    error_handler_timeout: int = 300  # Timeout für Operation (Sekunden), 0 = kein Timeout
    error_handler_on_error_target: str = ""  # Element-ID bei Fehler (nach allen Retries)
    error_handler_on_success_target: str = ""  # Element-ID bei Erfolg
    error_handler_log_errors: bool = True  # Fehler loggen?
    
    # State-Properties (NEU für STATE)
    state_name: str = ""  # Name des Zustands (z.B. "Eingereicht", "In Bearbeitung")
    state_type: str = "NORMAL"  # NORMAL, INITIAL, FINAL, ERROR
    state_entry_action: str = ""  # Aktion beim Eintritt (Element-ID oder Script)
    state_exit_action: str = ""  # Aktion beim Verlassen (Element-ID oder Script)
    state_transitions: List[Dict[str, Any]] = field(default_factory=list)  # Liste von Transitions
    state_timeout: int = 0  # Timeout im State (Sekunden), 0 = kein Timeout
    state_timeout_target: str = ""  # Element-ID bei Timeout
    
    # Interlock-Properties (NEU für INTERLOCK - Mutex/Semaphore)
    interlock_type: str = "MUTEX"  # MUTEX (exklusiv) oder SEMAPHORE (begrenzte Anzahl)
    interlock_resource_id: str = ""  # Eindeutige Ressourcen-ID (z.B. "db_connection", "printer_1")
    interlock_max_count: int = 1  # Maximale Anzahl gleichzeitiger Zugriffe (nur SEMAPHORE), MUTEX = 1
    interlock_timeout: int = 0  # Timeout beim Warten auf Lock (Sekunden), 0 = unbegrenzt warten
    interlock_on_locked_target: str = ""  # Element-ID wenn Lock nicht verfügbar (nach Timeout)
    interlock_auto_release: bool = True  # Lock automatisch nach Element-Durchlauf freigeben?
    
    # Canvas integration
    canvas_items: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate element after creation."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate element properties.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.element_id:
            raise ValueError("element_id cannot be empty")
        
        if not self.element_type:
            raise ValueError("element_type cannot be empty")
        
        if self.element_type not in ELEMENT_TYPES:
            logger.warning(f"Unknown element type: {self.element_type}")
        
        if not self.name:
            logger.warning(f"Element {self.element_id} has no name")
        
        if self.deadline_days < 0:
            raise ValueError("deadline_days cannot be negative")
    
    def center(self) -> Tuple[int, int]:
        """
        Get center coordinates of element.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        return (self.x, self.y)
    
    def move_to(self, x: int, y: int) -> VPBElement:
        """
        Create a new element at different position.
        
        Args:
            x: New x-coordinate
            y: New y-coordinate
            
        Returns:
            New VPBElement instance at new position
        """
        return VPBElement(
            element_id=self.element_id,
            element_type=self.element_type,
            name=self.name,
            x=x,
            y=y,
            description=self.description,
            responsible_authority=self.responsible_authority,
            legal_basis=self.legal_basis,
            deadline_days=self.deadline_days,
            geo_reference=self.geo_reference,
            ref_file=self.ref_file,
            ref_inline_content=self.ref_inline_content,
            ref_inline_path=self.ref_inline_path,
            ref_inline_error=self.ref_inline_error,
            ref_inline_truncated=self.ref_inline_truncated,
            ref_source_mtime=self.ref_source_mtime,
            original_element_type=self.original_element_type,
            members=self.members.copy(),
            collapsed=self.collapsed,
            loop_type=self.loop_type,
            loop_interval_minutes=self.loop_interval_minutes,
            loop_cron=self.loop_cron,
            loop_date=self.loop_date,
            loop_relative_days=self.loop_relative_days,
            loop_max_iterations=self.loop_max_iterations,
            counter_type=self.counter_type,
            counter_start_value=self.counter_start_value,
            counter_max_value=self.counter_max_value,
            counter_current_value=self.counter_current_value,
            counter_reset_on_max=self.counter_reset_on_max,
            counter_on_max_reached=self.counter_on_max_reached,
            canvas_items=self.canvas_items.copy(),
        )
    
    def clone(self, new_id: Optional[str] = None) -> VPBElement:
        """
        Create a deep copy of this element.
        
        Args:
            new_id: Optional new ID for the clone
            
        Returns:
            New VPBElement instance
        """
        return VPBElement(
            element_id=new_id or f"{self.element_id}_copy",
            element_type=self.element_type,
            name=f"{self.name} (copy)" if not new_id else self.name,
            x=self.x + 20,  # Offset slightly
            y=self.y + 20,
            description=self.description,
            responsible_authority=self.responsible_authority,
            legal_basis=self.legal_basis,
            deadline_days=self.deadline_days,
            geo_reference=self.geo_reference,
            ref_file=self.ref_file,
            ref_inline_content=self.ref_inline_content,
            ref_inline_path=self.ref_inline_path,
            ref_inline_error=self.ref_inline_error,
            ref_inline_truncated=self.ref_inline_truncated,
            ref_source_mtime=self.ref_source_mtime,
            original_element_type=self.original_element_type,
            members=self.members.copy(),
            collapsed=self.collapsed,
            loop_type=self.loop_type,
            loop_interval_minutes=self.loop_interval_minutes,
            loop_cron=self.loop_cron,
            loop_date=self.loop_date,
            loop_relative_days=self.loop_relative_days,
            loop_max_iterations=self.loop_max_iterations,
            counter_type=self.counter_type,
            counter_start_value=self.counter_start_value,
            counter_max_value=self.counter_max_value,
            counter_current_value=self.counter_start_value,  # Reset to start on clone
            counter_reset_on_max=self.counter_reset_on_max,
            counter_on_max_reached=self.counter_on_max_reached,
            condition_checks=self.condition_checks.copy() if self.condition_checks else [],
            condition_logic=self.condition_logic,
            condition_true_target=self.condition_true_target,
            condition_false_target=self.condition_false_target,
            error_handler_type=self.error_handler_type,
            error_handler_retry_count=self.error_handler_retry_count,
            error_handler_retry_delay=self.error_handler_retry_delay,
            error_handler_timeout=self.error_handler_timeout,
            error_handler_on_error_target=self.error_handler_on_error_target,
            error_handler_on_success_target=self.error_handler_on_success_target,
            error_handler_log_errors=self.error_handler_log_errors,
            # State-Properties
            state_name=self.state_name,
            state_type=self.state_type,
            state_entry_action=self.state_entry_action,
            state_exit_action=self.state_exit_action,
            state_transitions=self.state_transitions.copy() if self.state_transitions else [],
            state_timeout=self.state_timeout,
            state_timeout_target=self.state_timeout_target,
            # Interlock-Properties
            interlock_type=self.interlock_type,
            interlock_resource_id=self.interlock_resource_id,
            interlock_max_count=self.interlock_max_count,
            interlock_timeout=self.interlock_timeout,
            interlock_on_locked_target=self.interlock_on_locked_target,
            interlock_auto_release=self.interlock_auto_release,
            canvas_items=[],  # Don't copy canvas items
        )
    
    def is_container(self) -> bool:
        """Check if this element is a container."""
        return self.element_type == 'Container'
    
    def is_gateway(self) -> bool:
        """Check if this element is a gateway (AND/OR/XOR)."""
        return self.element_type in ('AND', 'OR', 'XOR')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert element to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'element_id': self.element_id,
            'element_type': self.element_type,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'description': self.description,
            'responsible_authority': self.responsible_authority,
            'legal_basis': self.legal_basis,
            'deadline_days': self.deadline_days,
            'geo_reference': self.geo_reference,
            'ref_file': self.ref_file,
            'ref_inline_content': self.ref_inline_content,
            'ref_inline_path': self.ref_inline_path,
            'ref_inline_error': self.ref_inline_error,
            'ref_inline_truncated': self.ref_inline_truncated,
            'ref_source_mtime': self.ref_source_mtime,
            'original_element_type': self.original_element_type,
            'members': self.members,
            'collapsed': self.collapsed,
            # Zeit-Properties (conditional)
            'loop_type': self.loop_type if self.loop_type != "none" else None,
            'loop_interval_minutes': self.loop_interval_minutes if self.loop_interval_minutes > 0 else None,
            'loop_cron': self.loop_cron if self.loop_cron else None,
            'loop_date': self.loop_date if self.loop_date else None,
            'loop_relative_days': self.loop_relative_days if self.loop_relative_days > 0 else None,
            'loop_max_iterations': self.loop_max_iterations if self.loop_max_iterations > 0 else None,
            # Counter-Properties (conditional)
            'counter_type': self.counter_type if self.element_type == 'COUNTER' else None,
            'counter_start_value': self.counter_start_value if self.element_type == 'COUNTER' else None,
            'counter_max_value': self.counter_max_value if self.element_type == 'COUNTER' else None,
            'counter_current_value': self.counter_current_value if self.element_type == 'COUNTER' else None,
            'counter_reset_on_max': self.counter_reset_on_max if self.element_type == 'COUNTER' else None,
            'counter_on_max_reached': self.counter_on_max_reached if self.counter_on_max_reached else None,
            # Condition-Properties (conditional)
            'condition_checks': self.condition_checks if self.element_type == 'CONDITION' and self.condition_checks else None,
            'condition_logic': self.condition_logic if self.element_type == 'CONDITION' else None,
            'condition_true_target': self.condition_true_target if self.condition_true_target else None,
            'condition_false_target': self.condition_false_target if self.condition_false_target else None,
            # Error-Handler-Properties (conditional)
            'error_handler_type': self.error_handler_type if self.element_type == 'ERROR_HANDLER' else None,
            'error_handler_retry_count': self.error_handler_retry_count if self.element_type == 'ERROR_HANDLER' else None,
            'error_handler_retry_delay': self.error_handler_retry_delay if self.element_type == 'ERROR_HANDLER' else None,
            'error_handler_timeout': self.error_handler_timeout if self.element_type == 'ERROR_HANDLER' else None,
            'error_handler_on_error_target': self.error_handler_on_error_target if self.error_handler_on_error_target else None,
            'error_handler_on_success_target': self.error_handler_on_success_target if self.error_handler_on_success_target else None,
            'error_handler_log_errors': self.error_handler_log_errors if self.element_type == 'ERROR_HANDLER' else None,
            # State-Properties (conditional)
            'state_name': self.state_name if self.state_name else None,
            'state_type': self.state_type if self.element_type == 'STATE' else None,
            'state_entry_action': self.state_entry_action if self.state_entry_action else None,
            'state_exit_action': self.state_exit_action if self.state_exit_action else None,
            'state_transitions': self.state_transitions if self.element_type == 'STATE' and self.state_transitions else None,
            'state_timeout': self.state_timeout if self.element_type == 'STATE' and self.state_timeout > 0 else None,
            'state_timeout_target': self.state_timeout_target if self.state_timeout_target else None,
            # Interlock-Properties (conditional)
            'interlock_type': self.interlock_type if self.element_type == 'INTERLOCK' else None,
            'interlock_resource_id': self.interlock_resource_id if self.interlock_resource_id else None,
            'interlock_max_count': self.interlock_max_count if self.element_type == 'INTERLOCK' else None,
            'interlock_timeout': self.interlock_timeout if self.element_type == 'INTERLOCK' and self.interlock_timeout > 0 else None,
            'interlock_on_locked_target': self.interlock_on_locked_target if self.interlock_on_locked_target else None,
            'interlock_auto_release': self.interlock_auto_release if self.element_type == 'INTERLOCK' else None,
            # Note: canvas_items are transient and not serialized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VPBElement:
        """
        Create element from dictionary.
        
        Args:
            data: Dictionary with element data
            
        Returns:
            New VPBElement instance
        """
        return cls(
            element_id=data['element_id'],
            element_type=data['element_type'],
            name=data['name'],
            x=int(data['x']),
            y=int(data['y']),
            description=data.get('description', ''),
            responsible_authority=data.get('responsible_authority', ''),
            legal_basis=data.get('legal_basis', ''),
            deadline_days=int(data.get('deadline_days', 0)),
            geo_reference=data.get('geo_reference', ''),
            ref_file=data.get('ref_file', ''),
            ref_inline_content=data.get('ref_inline_content'),
            ref_inline_path=data.get('ref_inline_path'),
            ref_inline_error=data.get('ref_inline_error'),
            ref_inline_truncated=bool(data.get('ref_inline_truncated', False)),
            ref_source_mtime=data.get('ref_source_mtime'),
            original_element_type=data.get('original_element_type'),
            members=data.get('members', []),
            collapsed=bool(data.get('collapsed', False)),
            # Zeit-Properties
            loop_type=data.get('loop_type') or 'none',
            loop_interval_minutes=int(data.get('loop_interval_minutes') or 0),
            loop_cron=data.get('loop_cron') or '',
            loop_date=data.get('loop_date') or '',
            loop_relative_days=int(data.get('loop_relative_days') or 0),
            loop_max_iterations=int(data.get('loop_max_iterations') or 0),
            # Counter-Properties
            counter_type=data.get('counter_type') or 'UP',
            counter_start_value=int(data.get('counter_start_value') or 0),
            counter_max_value=int(data.get('counter_max_value') or 100),
            counter_current_value=int(data.get('counter_current_value') or 0),
            counter_reset_on_max=bool(data.get('counter_reset_on_max', False)),
            counter_on_max_reached=data.get('counter_on_max_reached') or '',
            # Condition-Properties
            condition_checks=data.get('condition_checks') or [],
            condition_logic=data.get('condition_logic') or 'AND',
            condition_true_target=data.get('condition_true_target') or '',
            condition_false_target=data.get('condition_false_target') or '',
            # Error-Handler-Properties
            error_handler_type=data.get('error_handler_type') or 'RETRY',
            error_handler_retry_count=int(data.get('error_handler_retry_count') or 3),
            error_handler_retry_delay=int(data.get('error_handler_retry_delay') or 60),
            error_handler_timeout=int(data.get('error_handler_timeout') or 300),
            error_handler_on_error_target=data.get('error_handler_on_error_target') or '',
            error_handler_on_success_target=data.get('error_handler_on_success_target') or '',
            error_handler_log_errors=bool(data.get('error_handler_log_errors', True)),
            # State-Properties
            state_name=data.get('state_name') or '',
            state_type=data.get('state_type') or 'NORMAL',
            state_entry_action=data.get('state_entry_action') or '',
            state_exit_action=data.get('state_exit_action') or '',
            state_transitions=data.get('state_transitions') or [],
            state_timeout=int(data.get('state_timeout') or 0),
            state_timeout_target=data.get('state_timeout_target') or '',
            # Interlock-Properties
            interlock_type=data.get('interlock_type') or 'MUTEX',
            interlock_resource_id=data.get('interlock_resource_id') or '',
            interlock_max_count=int(data.get('interlock_max_count') or 1),
            interlock_timeout=int(data.get('interlock_timeout') or 0),
            interlock_on_locked_target=data.get('interlock_on_locked_target') or '',
            interlock_auto_release=bool(data.get('interlock_auto_release', True)),
            canvas_items=[],  # Don't restore canvas items
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"VPBElement(id='{self.element_id}', "
            f"type='{self.element_type}', "
            f"name='{self.name}', "
            f"pos=({self.x}, {self.y}))"
        )


class ElementFactory:
    """
    Factory for creating VPB elements.
    
    Provides convenient methods to create elements with proper defaults.
    """
    
    @staticmethod
    def create(
        element_type: str,
        x: int,
        y: int,
        name: Optional[str] = None,
        element_id: Optional[str] = None,
        **kwargs
    ) -> VPBElement:
        """
        Create a new VPB element.
        
        Args:
            element_type: Type of element
            x: X-coordinate
            y: Y-coordinate
            name: Element name (auto-generated if None)
            element_id: Element ID (auto-generated if None)
            **kwargs: Additional properties
            
        Returns:
            New VPBElement instance
        """
        if element_id is None:
            element_id = f"elem_{uuid4().hex[:8]}"
        
        if name is None:
            name = ELEMENT_TYPES.get(element_type, element_type)
        
        return VPBElement(
            element_id=element_id,
            element_type=element_type,
            name=name,
            x=x,
            y=y,
            **kwargs
        )
    
    @staticmethod
    def create_prozess(x: int, y: int, name: str = "Prozess") -> VPBElement:
        """Create a Prozess element."""
        return ElementFactory.create('Prozess', x, y, name)
    
    @staticmethod
    def create_vorprozess(x: int, y: int, name: str = "Vor-Prozess") -> VPBElement:
        """Create a VorProzess element."""
        return ElementFactory.create('VorProzess', x, y, name)
    
    @staticmethod
    def create_nachprozess(x: int, y: int, name: str = "Nach-Prozess") -> VPBElement:
        """Create a NachProzess element."""
        return ElementFactory.create('NachProzess', x, y, name)
    
    @staticmethod
    def create_entscheidung(x: int, y: int, name: str = "Entscheidung") -> VPBElement:
        """Create an Entscheidung element."""
        return ElementFactory.create('Entscheidung', x, y, name)
    
    @staticmethod
    def create_gateway(
        gateway_type: str,
        x: int,
        y: int,
        name: Optional[str] = None
    ) -> VPBElement:
        """
        Create a gateway element.
        
        Args:
            gateway_type: 'AND', 'OR', or 'XOR'
            x: X-coordinate
            y: Y-coordinate
            name: Gateway name
            
        Returns:
            New gateway element
        """
        if gateway_type not in ('AND', 'OR', 'XOR'):
            raise ValueError(f"Invalid gateway type: {gateway_type}")
        
        if name is None:
            name = f"{gateway_type}-Gateway"
        
        return ElementFactory.create(gateway_type, x, y, name)
    
    @staticmethod
    def create_container(
        x: int,
        y: int,
        name: str = "Container",
        members: Optional[List[str]] = None
    ) -> VPBElement:
        """Create a Container element."""
        return ElementFactory.create(
            'Container',
            x, y,
            name,
            members=members or []
        )


__all__ = ['VPBElement', 'ElementFactory', 'ELEMENT_TYPES']
