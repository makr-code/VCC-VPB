"""
Validation Service
==================

Service for validating VPB process documents.

This service performs comprehensive validation including:
- Process flow validation (dead ends, unreachable elements)
- Structural validation (orphaned connections, missing elements)
- Naming conventions and best practices
- Completeness checks
- Business rule validation

Example:
    ```python
    from vpb.services.validation_service import ValidationService
    from vpb.models import DocumentModel
    
    service = ValidationService()
    
    # Validate document
    result = service.validate_document(doc)
    
    if not result.is_valid:
        for issue in result.errors:
            print(f"ERROR: {issue.message}")
        for warning in result.warnings:
            print(f"WARNING: {warning.message}")
    ```
"""

import logging
from typing import List, Set, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from vpb.models.document import DocumentModel
from vpb.models.element import VPBElement
from vpb.models.connection import VPBConnection

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Blocks saving/export
    WARNING = "warning"  # Should be fixed but not blocking
    INFO = "info"        # Suggestions for improvement


@dataclass
class ValidationIssue:
    """
    Represents a validation issue.
    
    Attributes:
        severity: Issue severity (error/warning/info)
        category: Issue category (flow/structure/naming/etc.)
        message: Human-readable message
        element_id: ID of related element (if applicable)
        connection_id: ID of related connection (if applicable)
        suggestion: Optional suggestion how to fix
    """
    severity: IssueSeverity
    category: str
    message: str
    element_id: Optional[str] = None
    connection_id: Optional[str] = None
    suggestion: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation."""
        parts = [f"[{self.severity.upper()}]", f"({self.category})", self.message]
        if self.element_id:
            parts.append(f"[Element: {self.element_id}]")
        if self.connection_id:
            parts.append(f"[Connection: {self.connection_id}]")
        return " ".join(parts)


@dataclass
class ValidationResult:
    """
    Result of document validation.
    
    Attributes:
        is_valid: Whether document is valid (no errors)
        errors: List of error issues
        warnings: List of warning issues
        info: List of info issues
        stats: Statistics about the validation
    """
    is_valid: bool = True
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(
        self,
        category: str,
        message: str,
        element_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> None:
        """Add an error issue."""
        self.errors.append(ValidationIssue(
            severity=IssueSeverity.ERROR,
            category=category,
            message=message,
            element_id=element_id,
            connection_id=connection_id,
            suggestion=suggestion
        ))
        self.is_valid = False
    
    def add_warning(
        self,
        category: str,
        message: str,
        element_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> None:
        """Add a warning issue."""
        self.warnings.append(ValidationIssue(
            severity=IssueSeverity.WARNING,
            category=category,
            message=message,
            element_id=element_id,
            connection_id=connection_id,
            suggestion=suggestion
        ))
    
    def add_info(
        self,
        category: str,
        message: str,
        element_id: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> None:
        """Add an info issue."""
        self.info.append(ValidationIssue(
            severity=IssueSeverity.INFO,
            category=category,
            message=message,
            element_id=element_id,
            suggestion=suggestion
        ))
    
    @property
    def all_issues(self) -> List[ValidationIssue]:
        """Get all issues (errors + warnings + info)."""
        return self.errors + self.warnings + self.info
    
    @property
    def issue_count(self) -> int:
        """Total number of issues."""
        return len(self.all_issues)
    
    def __str__(self) -> str:
        """String representation."""
        status = "VALID" if self.is_valid else "INVALID"
        return (
            f"ValidationResult: {status}\n"
            f"  Errors: {len(self.errors)}\n"
            f"  Warnings: {len(self.warnings)}\n"
            f"  Info: {len(self.info)}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ValidationResult to dictionary format.
        
        Returns dict with:
            - errors: List of error dicts
            - warnings: List of warning dicts
            - info: List of info dicts
            - element_count: Element count from stats
            - connection_count: Connection count from stats
        """
        return {
            'errors': [
                {
                    'rule': issue.category,
                    'message': issue.message,
                    'element_id': issue.element_id,
                    'connection_id': issue.connection_id
                }
                for issue in self.errors
            ],
            'warnings': [
                {
                    'rule': issue.category,
                    'message': issue.message,
                    'element_id': issue.element_id,
                    'connection_id': issue.connection_id
                }
                for issue in self.warnings
            ],
            'info': [
                {
                    'rule': issue.category,
                    'message': issue.message,
                    'element_id': issue.element_id,
                    'connection_id': issue.connection_id
                }
                for issue in self.info
            ],
            'element_count': self.stats.get('element_count', 0),
            'connection_count': self.stats.get('connection_count', 0)
        }


class ValidationService:
    """
    Service for validating VPB documents.
    
    Performs various validation checks on documents including:
    - Process flow validation
    - Structural validation
    - Naming conventions
    - Completeness checks
    
    Example:
        ```python
        service = ValidationService()
        result = service.validate_document(doc)
        
        if not result.is_valid:
            for error in result.errors:
                print(error)
        ```
    """
    
    def __init__(
        self,
        check_naming: bool = True,
        check_flow: bool = True,
        check_completeness: bool = True,
        min_name_length: int = 3,
        max_name_length: int = 100
    ):
        """
        Initialize ValidationService.
        
        Args:
            check_naming: Enable naming convention checks
            check_flow: Enable process flow checks
            check_completeness: Enable completeness checks
            min_name_length: Minimum element name length
            max_name_length: Maximum element name length
        """
        self.check_naming = check_naming
        self.check_flow = check_flow
        self.check_completeness = check_completeness
        self.min_name_length = min_name_length
        self.max_name_length = max_name_length
        
        logger.info(
            f"ValidationService initialized (naming={check_naming}, "
            f"flow={check_flow}, completeness={check_completeness})"
        )
    
    def validate_document(self, doc: DocumentModel) -> ValidationResult:
        """
        Perform comprehensive validation on a document.
        
        Args:
            doc: DocumentModel to validate
        
        Returns:
            ValidationResult with all issues found
        
        Example:
            ```python
            result = service.validate_document(doc)
            print(f"Valid: {result.is_valid}")
            print(f"Issues: {result.issue_count}")
            ```
        """
        logger.info(f"Validating document: {doc.metadata.title}")
        
        result = ValidationResult()
        
        # Collect stats
        result.stats = {
            'element_count': doc.get_element_count(),
            'connection_count': doc.get_connection_count(),
            'elements_by_type': self._count_elements_by_type(doc),
        }
        
        # Run validation checks
        self._validate_structure(doc, result)
        
        if self.check_flow:
            self._validate_flow(doc, result)
        
        if self.check_naming:
            self._validate_naming(doc, result)
        
        if self.check_completeness:
            self._validate_completeness(doc, result)
        
        # Validate special elements (COUNTER, etc.)
        self._validate_special_elements(doc, result)
        
        logger.info(
            f"Validation complete: {len(result.errors)} errors, "
            f"{len(result.warnings)} warnings, {len(result.info)} info"
        )
        
        return result
    
    def _validate_structure(self, doc: DocumentModel, result: ValidationResult) -> None:
        """
        Validate document structure (orphaned connections, etc.).
        
        Args:
            doc: Document to validate
            result: Result object to add issues to
        """
        # Use DocumentModel's built-in validation
        structural_errors = doc.validate()
        for error in structural_errors:
            result.add_error('structure', error)
        
        # Check for empty document
        if doc.is_empty():
            result.add_warning(
                'structure',
                'Document is empty',
                suggestion='Add at least one element to the process'
            )
    
    def _validate_flow(self, doc: DocumentModel, result: ValidationResult) -> None:
        """
        Validate process flow (dead ends, unreachable elements, cycles).
        
        Args:
            doc: Document to validate
            result: Result object to add issues to
        """
        elements = doc.get_all_elements()
        
        if not elements:
            return  # Nothing to validate
        
        # Find start elements (VorProzess or elements with no incoming connections)
        start_elements = self._find_start_elements(doc)
        
        # Find end elements (NachProzess or elements with no outgoing connections)
        end_elements = self._find_end_elements(doc)
        
        # Check for missing start/end
        if not start_elements:
            result.add_warning(
                'flow',
                'No start elements found (VorProzess or elements without incoming connections)',
                suggestion='Add a VorProzess element or ensure at least one element has no incoming connections'
            )
        
        if not end_elements:
            result.add_warning(
                'flow',
                'No end elements found (NachProzess or elements without outgoing connections)',
                suggestion='Add a NachProzess element or ensure at least one element has no outgoing connections'
            )
        
        # Check for unreachable elements
        if start_elements:
            reachable = self._find_reachable_elements(doc, start_elements)
            unreachable = set(e.element_id for e in elements) - reachable
            
            for element_id in unreachable:
                element = doc.get_element(element_id)
                result.add_error(
                    'flow',
                    f'Element "{element.name}" is unreachable from start',
                    element_id=element_id,
                    suggestion='Add a connection from a start element or another reachable element'
                )
        
        # Check for dead ends (elements that don't lead to end)
        if end_elements:
            can_reach_end = self._find_elements_reaching_end(doc, end_elements)
            dead_ends = set(e.element_id for e in elements) - can_reach_end - set(e.element_id for e in end_elements)
            
            for element_id in dead_ends:
                element = doc.get_element(element_id)
                # Only warn about dead ends if they have outgoing connections
                # (if no outgoing, they ARE end elements)
                if doc.get_outgoing_connections(element_id):
                    result.add_warning(
                        'flow',
                        f'Element "{element.name}" doesn\'t lead to any end element',
                        element_id=element_id,
                        suggestion='Add a path to an end element or remove unnecessary connections'
                    )
        
        # Check for decision/gateway elements
        self._validate_decision_elements(doc, result)
    
    def _validate_naming(self, doc: DocumentModel, result: ValidationResult) -> None:
        """
        Validate naming conventions.
        
        Args:
            doc: Document to validate
            result: Result object to add issues to
        """
        seen_names: Dict[str, str] = {}  # name -> element_id
        
        for element in doc.get_all_elements():
            name = element.name.strip()
            
            # Check empty names
            if not name:
                result.add_error(
                    'naming',
                    'Element has empty name',
                    element_id=element.element_id,
                    suggestion='Provide a descriptive name for this element'
                )
                continue
            
            # Check name length
            if len(name) < self.min_name_length:
                result.add_warning(
                    'naming',
                    f'Element name "{name}" is too short (min: {self.min_name_length} characters)',
                    element_id=element.element_id,
                    suggestion='Use a more descriptive name'
                )
            
            if len(name) > self.max_name_length:
                result.add_warning(
                    'naming',
                    f'Element name "{name}" is too long (max: {self.max_name_length} characters)',
                    element_id=element.element_id,
                    suggestion='Use a shorter, more concise name'
                )
            
            # Check for duplicate names
            if name in seen_names:
                result.add_warning(
                    'naming',
                    f'Duplicate element name "{name}"',
                    element_id=element.element_id,
                    suggestion=f'Element name is also used by element {seen_names[name]}'
                )
            else:
                seen_names[name] = element.element_id
            
            # Check naming conventions (should start with uppercase)
            if name and not name[0].isupper():
                result.add_info(
                    'naming',
                    f'Element name "{name}" should start with uppercase letter',
                    element_id=element.element_id,
                    suggestion='Follow naming convention: start with uppercase'
                )
    
    def _validate_completeness(self, doc: DocumentModel, result: ValidationResult) -> None:
        """
        Validate document completeness.
        
        Args:
            doc: Document to validate
            result: Result object to add issues to
        """
        # Check metadata
        if not doc.metadata.title or doc.metadata.title == "Untitled Process":
            result.add_warning(
                'completeness',
                'Document has no title',
                suggestion='Provide a meaningful title for this process'
            )
        
        if not doc.metadata.description:
            result.add_info(
                'completeness',
                'Document has no description',
                suggestion='Add a description explaining the purpose of this process'
            )
        
        if not doc.metadata.author:
            result.add_info(
                'completeness',
                'Document has no author',
                suggestion='Specify who created this process'
            )
        
        # Check if elements have descriptions
        elements_without_description = [
            e for e in doc.get_all_elements()
            if not e.description or not e.description.strip()
        ]
        
        if elements_without_description:
            result.add_info(
                'completeness',
                f'{len(elements_without_description)} elements have no description',
                suggestion='Add descriptions to elements for better documentation'
            )
    
    def _validate_decision_elements(self, doc: DocumentModel, result: ValidationResult) -> None:
        """
        Validate decision and gateway elements.
        
        Args:
            doc: Document to validate
            result: Result object to add issues to
        """
        for element in doc.get_all_elements():
            if element.element_type == 'Entscheidung':
                outgoing = doc.get_outgoing_connections(element.element_id)
                
                if len(outgoing) < 2:
                    result.add_warning(
                        'flow',
                        f'Decision "{element.name}" has less than 2 outgoing connections',
                        element_id=element.element_id,
                        suggestion='Decisions should have at least 2 alternative paths'
                    )
                
                if len(outgoing) > 4:
                    result.add_info(
                        'flow',
                        f'Decision "{element.name}" has many ({len(outgoing)}) outgoing connections',
                        element_id=element.element_id,
                        suggestion='Consider breaking down complex decisions'
                    )
            
            # Check gateways
            if element.element_type.startswith('Gateway'):
                incoming = doc.get_incoming_connections(element.element_id)
                outgoing = doc.get_outgoing_connections(element.element_id)
                
                if len(incoming) == 0:
                    result.add_error(
                        'flow',
                        f'Gateway "{element.name}" has no incoming connections',
                        element_id=element.element_id,
                        suggestion='Gateways must have at least one incoming connection'
                    )
                
                if len(outgoing) == 0:
                    result.add_error(
                        'flow',
                        f'Gateway "{element.name}" has no outgoing connections',
                        element_id=element.element_id,
                        suggestion='Gateways must have at least one outgoing connection'
                    )
    
    def _find_start_elements(self, doc: DocumentModel) -> List[VPBElement]:
        """Find elements that are process starts."""
        start_elements = []
        
        for element in doc.get_all_elements():
            # VorProzess is always a start
            if element.element_type == 'VorProzess':
                start_elements.append(element)
            # Elements with no incoming connections
            elif not doc.get_incoming_connections(element.element_id):
                start_elements.append(element)
        
        return start_elements
    
    def _find_end_elements(self, doc: DocumentModel) -> List[VPBElement]:
        """Find elements that are process ends."""
        end_elements = []
        
        for element in doc.get_all_elements():
            # NachProzess is always an end
            if element.element_type == 'NachProzess':
                end_elements.append(element)
            # Elements with no outgoing connections
            elif not doc.get_outgoing_connections(element.element_id):
                end_elements.append(element)
        
        return end_elements
    
    def _find_reachable_elements(
        self,
        doc: DocumentModel,
        start_elements: List[VPBElement]
    ) -> Set[str]:
        """
        Find all elements reachable from start elements (BFS).
        
        Args:
            doc: Document
            start_elements: List of start elements
        
        Returns:
            Set of reachable element IDs
        """
        reachable = set()
        queue = [e.element_id for e in start_elements]
        
        while queue:
            current_id = queue.pop(0)
            
            if current_id in reachable:
                continue
            
            reachable.add(current_id)
            
            # Add all elements connected from current (using element_id)
            for conn in doc.get_outgoing_connections(current_id):
                if conn.target_element.element_id not in reachable:
                    queue.append(conn.target_element.element_id)
        
        return reachable
    
    def _find_elements_reaching_end(
        self,
        doc: DocumentModel,
        end_elements: List[VPBElement]
    ) -> Set[str]:
        """
        Find all elements that can reach an end element (reverse BFS).
        
        Args:
            doc: Document
            end_elements: List of end elements
        
        Returns:
            Set of element IDs that can reach end
        """
        can_reach_end = set()
        queue = [e.element_id for e in end_elements]
        
        while queue:
            current_id = queue.pop(0)
            
            if current_id in can_reach_end:
                continue
            
            can_reach_end.add(current_id)
            
            # Add all elements connected to current (reverse direction, using element_id)
            for conn in doc.get_incoming_connections(current_id):
                if conn.source_element.element_id not in can_reach_end:
                    queue.append(conn.source_element.element_id)
        
        return can_reach_end
    
    def _count_elements_by_type(self, doc: DocumentModel) -> Dict[str, int]:
        """Count elements by type."""
        counts: Dict[str, int] = {}
        
        for element in doc.get_all_elements():
            element_type = element.element_type
            counts[element_type] = counts.get(element_type, 0) + 1
        
        return counts
    
    def _validate_special_elements(self, doc: DocumentModel, result: ValidationResult) -> None:
        """
        Validate special elements (COUNTER, CONDITION, ERROR_HANDLER, STATE, INTERLOCK, etc.).
        
        Args:
            doc: Document to validate
            result: Result object to add issues to
        """
        counter_validator = CounterValidator()
        condition_validator = ConditionValidator()
        error_handler_validator = ErrorHandlerValidator()
        state_validator = StateValidator()
        interlock_validator = InterlockValidator()
        
        for element in doc.get_all_elements():
            # Validate COUNTER elements
            if element.element_type == "COUNTER":
                counter_validator.validate_counter(element, doc, result)
            
            # Validate CONDITION elements
            elif element.element_type == "CONDITION":
                condition_validator.validate_condition(element, doc, result)
            
            # Validate ERROR_HANDLER elements
            elif element.element_type == "ERROR_HANDLER":
                error_handler_validator.validate_error_handler(element, doc, result)
            
            # Validate STATE elements
            elif element.element_type == "STATE":
                state_validator.validate_state(element, doc, result)
            
            # Validate INTERLOCK elements
            elif element.element_type == "INTERLOCK":
                interlock_validator.validate_interlock(element, doc, result)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ValidationService(naming={self.check_naming}, "
            f"flow={self.check_flow}, completeness={self.check_completeness})"
        )


class CounterValidator:
    """
    Validator for COUNTER elements.
    
    Validates:
    1. counter_max_value > counter_start_value
    2. counter_current_value in range [start, max]
    3. counter_on_max_reached is valid element ID
    4. Counter has at least 1 incoming connection
    5. Counter has outgoing connection (unless on_max_reached is set)
    """
    
    def validate_counter(
        self,
        element: VPBElement,
        doc: DocumentModel,
        result: ValidationResult
    ) -> None:
        """
        Validate COUNTER element.
        
        Args:
            element: Counter element to validate
            doc: Document containing the element
            result: Validation result to add issues to
        """
        if element.element_type != "COUNTER":
            return
        
        # Rule 1: Maximum > Start
        start_value = getattr(element, "counter_start_value", 0)
        max_value = getattr(element, "counter_max_value", 100)
        
        if max_value <= start_value:
            result.add_error(
                category="counter",
                message=f"Counter maximum ({max_value}) must be greater than start ({start_value})",
                element_id=element.element_id,
                suggestion=f"Set counter_max_value > {start_value}"
            )
        
        # Rule 2: Current value in range
        current_value = getattr(element, "counter_current_value", 0)
        counter_type = getattr(element, "counter_type", "UP")
        
        if counter_type == "UP":
            if not (start_value <= current_value <= max_value):
                result.add_warning(
                    category="counter",
                    message=f"Current value ({current_value}) is outside valid range [{start_value}, {max_value}]",
                    element_id=element.element_id,
                    suggestion=f"Set counter_current_value between {start_value} and {max_value}"
                )
        elif counter_type == "DOWN":
            if not (0 <= current_value <= start_value):
                result.add_warning(
                    category="counter",
                    message=f"Current value ({current_value}) is outside valid range [0, {start_value}]",
                    element_id=element.element_id,
                    suggestion=f"Set counter_current_value between 0 and {start_value}"
                )
        
        # Rule 3: On-Max element exists
        on_max_reached = getattr(element, "counter_on_max_reached", "")
        if on_max_reached:
            # Check if element exists
            target_element = doc.get_element(on_max_reached)
            if not target_element:
                result.add_error(
                    category="counter",
                    message=f"Target element '{on_max_reached}' for on_max_reached does not exist",
                    element_id=element.element_id,
                    suggestion="Specify valid element ID or leave empty"
                )
        
        # Rule 4: Counter has at least 1 incoming connection
        incoming = doc.get_incoming_connections(element.element_id)
        if len(incoming) == 0:
            result.add_warning(
                category="counter",
                message="Counter has no incoming connections (will never be incremented)",
                element_id=element.element_id,
                suggestion="Connect at least one element to this counter"
            )
        
        # Rule 5: Counter has outgoing connection (unless on_max_reached is set)
        outgoing = doc.get_outgoing_connections(element.element_id)
        if len(outgoing) == 0 and not on_max_reached:
            result.add_warning(
                category="counter",
                message="Counter has no outgoing connections and no on_max_reached target",
                element_id=element.element_id,
                suggestion="Connect counter to next element or set on_max_reached"
            )
        
        # Additional check: Counter type validity
        valid_types = ["UP", "DOWN", "UP_DOWN"]
        if counter_type not in valid_types:
            result.add_error(
                category="counter",
                message=f"Invalid counter_type '{counter_type}'. Must be one of: {', '.join(valid_types)}",
                element_id=element.element_id,
                suggestion=f"Set counter_type to UP, DOWN, or UP_DOWN"
            )
        
        # Info: Suggest using reset if counter is in a loop
        if len(incoming) > 1 or any(conn.source_element.element_id == element.element_id for conn in outgoing):
            reset_on_max = getattr(element, "counter_reset_on_max", False)
            if not reset_on_max:
                result.add_info(
                    category="counter",
                    message="Counter appears to be in a loop but reset_on_max is disabled",
                    element_id=element.element_id,
                    suggestion="Consider enabling 'reset_on_max' for looping counters"
                )


class ConditionValidator:
    """Validiert CONDITION-Elemente."""
    
    VALID_OPERATORS = ["==", "!=", "<", ">", "<=", ">=", "contains", "regex"]
    
    def validate_condition(self, element, doc, result):
        """
        Validiert ein CONDITION-Element.
        
        Args:
            element: Das zu validierende Element
            doc: Das VPBDocument
            result: ValidationResult zum Hinzufügen von Fehlern/Warnungen
        """
        # Regel 1: Mindestens 1 Check erforderlich [ERROR]
        condition_checks = getattr(element, "condition_checks", [])
        if not condition_checks or len(condition_checks) == 0:
            result.add_error(
                category="condition",
                message="CONDITION must have at least 1 check",
                element_id=element.element_id,
                suggestion="Add at least one condition check using the Properties Panel"
            )
            return  # Keine weiteren Validierungen wenn keine Checks vorhanden
        
        # Regel 2: Alle Operatoren müssen gültig sein [ERROR]
        for idx, check in enumerate(condition_checks):
            operator = check.get("operator", "")
            if operator not in self.VALID_OPERATORS:
                result.add_error(
                    category="condition",
                    message=f"Invalid operator '{operator}' in check #{idx+1}",
                    element_id=element.element_id,
                    suggestion=f"Use one of: {', '.join(self.VALID_OPERATORS)}"
                )
            
            # Zusätzliche Validierung: Field und Value sollten nicht leer sein
            field = check.get("field", "").strip()
            value = check.get("value", "").strip()
            if not field:
                result.add_error(
                    category="condition",
                    message=f"Empty field name in check #{idx+1}",
                    element_id=element.element_id,
                    suggestion="Specify a field name to check"
                )
            if not value:
                result.add_error(
                    category="condition",
                    message=f"Empty value in check #{idx+1}",
                    element_id=element.element_id,
                    suggestion="Specify a value to compare against"
                )
        
        # Regel 3: TRUE-Target muss existieren wenn gesetzt [ERROR]
        condition_true_target = getattr(element, "condition_true_target", "")
        if condition_true_target:
            target_element = doc.get_element(condition_true_target)
            if not target_element:
                result.add_error(
                    category="condition",
                    message=f"TRUE target element '{condition_true_target}' does not exist",
                    element_id=element.element_id,
                    suggestion="Select an existing element as TRUE target or leave empty"
                )
        else:
            result.add_warning(
                category="condition",
                message="CONDITION has no TRUE target defined",
                element_id=element.element_id,
                suggestion="Define where to go when condition is TRUE"
            )
        
        # Regel 4: FALSE-Target muss existieren wenn gesetzt [ERROR]
        condition_false_target = getattr(element, "condition_false_target", "")
        if condition_false_target:
            target_element = doc.get_element(condition_false_target)
            if not target_element:
                result.add_error(
                    category="condition",
                    message=f"FALSE target element '{condition_false_target}' does not exist",
                    element_id=element.element_id,
                    suggestion="Select an existing element as FALSE target or leave empty"
                )
        else:
            result.add_warning(
                category="condition",
                message="CONDITION has no FALSE target defined",
                element_id=element.element_id,
                suggestion="Define where to go when condition is FALSE"
            )
        
        # Regel 5: Sollte eingehende Verbindungen haben [WARNING]
        incoming = doc.get_incoming_connections(element.element_id)
        if not incoming:
            result.add_warning(
                category="condition",
                message="CONDITION has no incoming connections",
                element_id=element.element_id,
                suggestion="Connect an element to this CONDITION to activate it"
            )


class ErrorHandlerValidator:
    """Validiert ERROR_HANDLER-Elemente."""
    
    VALID_HANDLER_TYPES = ["RETRY", "FALLBACK", "NOTIFY", "ABORT"]
    
    def validate_error_handler(self, element, doc, result):
        """
        Validiert ein ERROR_HANDLER-Element.
        
        Args:
            element: Das zu validierende Element
            doc: Das VPBDocument
            result: ValidationResult zum Hinzufügen von Fehlern/Warnungen
        """
        # Regel 1: Handler-Type muss gültig sein [ERROR]
        handler_type = getattr(element, "error_handler_type", "RETRY")
        if handler_type not in self.VALID_HANDLER_TYPES:
            result.add_error(
                category="error_handler",
                message=f"Invalid handler type '{handler_type}'",
                element_id=element.element_id,
                suggestion=f"Use one of: {', '.join(self.VALID_HANDLER_TYPES)}"
            )
        
        # Regel 2: Retry-Count muss >= 0 sein [ERROR]
        retry_count = getattr(element, "error_handler_retry_count", 3)
        if retry_count < 0:
            result.add_error(
                category="error_handler",
                message=f"Retry count cannot be negative (current: {retry_count})",
                element_id=element.element_id,
                suggestion="Set retry count to 0 or higher"
            )
        
        # Regel 3: Delay muss > 0 sein wenn retry_count > 0 [ERROR]
        retry_delay = getattr(element, "error_handler_retry_delay", 60)
        if handler_type == "RETRY" and retry_count > 0 and retry_delay <= 0:
            result.add_error(
                category="error_handler",
                message=f"Retry delay must be positive when retry count > 0 (current: {retry_delay})",
                element_id=element.element_id,
                suggestion="Set retry delay to a positive value (e.g., 60 seconds)"
            )
        
        # Regel 4: Timeout >= 0, Warnung wenn 0 [WARNING]
        timeout = getattr(element, "error_handler_timeout", 300)
        if timeout < 0:
            result.add_error(
                category="error_handler",
                message=f"Timeout cannot be negative (current: {timeout})",
                element_id=element.element_id,
                suggestion="Set timeout to 0 (no timeout) or a positive value"
            )
        elif timeout == 0:
            result.add_warning(
                category="error_handler",
                message="Timeout is disabled (0 = no timeout)",
                element_id=element.element_id,
                suggestion="Consider setting a timeout to prevent indefinite waits"
            )
        
        # Regel 5: Error-Target muss existieren wenn gesetzt [ERROR]
        error_target = getattr(element, "error_handler_on_error_target", "")
        if error_target:
            target_element = doc.get_element(error_target)
            if not target_element:
                result.add_error(
                    category="error_handler",
                    message=f"Error target element '{error_target}' does not exist",
                    element_id=element.element_id,
                    suggestion="Select an existing element as error target or leave empty"
                )
        elif handler_type in ["FALLBACK", "RETRY"]:
            result.add_warning(
                category="error_handler",
                message=f"ERROR_HANDLER ({handler_type}) has no error target defined",
                element_id=element.element_id,
                suggestion="Define where to go when error handling fails"
            )
        
        # Regel 6: Success-Target muss existieren wenn gesetzt [WARNING]
        success_target = getattr(element, "error_handler_on_success_target", "")
        if success_target:
            target_element = doc.get_element(success_target)
            if not target_element:
                result.add_warning(
                    category="error_handler",
                    message=f"Success target element '{success_target}' does not exist",
                    element_id=element.element_id,
                    suggestion="Select an existing element as success target or leave empty"
                )
        
        # Regel 7: Sollte eingehende Verbindungen haben [WARNING]
        incoming = doc.get_incoming_connections(element.element_id)
        if not incoming:
            result.add_warning(
                category="error_handler",
                message="ERROR_HANDLER has no incoming connections",
                element_id=element.element_id,
                suggestion="Connect an element to this ERROR_HANDLER to activate it"
            )


class StateValidator:
    """Validiert STATE-Elemente (Zustandsautomaten)."""
    
    VALID_STATE_TYPES = ["NORMAL", "INITIAL", "FINAL", "ERROR"]
    
    def validate_state(self, element, doc, result):
        """
        Validiert ein STATE-Element.
        
        Args:
            element: Das zu validierende Element
            doc: Das VPBDocument
            result: ValidationResult zum Hinzufügen von Fehlern/Warnungen
        """
        # Regel 1: State-Name darf nicht leer sein [ERROR]
        state_name = getattr(element, "state_name", "").strip()
        if not state_name:
            result.add_error(
                category="state",
                message="STATE element must have a name",
                element_id=element.element_id,
                suggestion="Enter a descriptive state name (e.g., 'Eingereicht', 'In Bearbeitung')"
            )
        
        # Regel 2: State-Type muss gültig sein [ERROR]
        state_type = getattr(element, "state_type", "NORMAL")
        if state_type not in self.VALID_STATE_TYPES:
            result.add_error(
                category="state",
                message=f"Invalid state type '{state_type}'",
                element_id=element.element_id,
                suggestion=f"Use one of: {', '.join(self.VALID_STATE_TYPES)}"
            )
        
        # Regel 3: Nur ein INITIAL-State im gesamten Dokument [ERROR]
        if state_type == "INITIAL":
            initial_states = [
                el for el in doc.get_all_elements()
                if el.element_type == "STATE" and getattr(el, "state_type", "NORMAL") == "INITIAL"
            ]
            if len(initial_states) > 1:
                result.add_error(
                    category="state",
                    message=f"Multiple INITIAL states found ({len(initial_states)} total)",
                    element_id=element.element_id,
                    suggestion="A state machine can only have one INITIAL state. Change other states to NORMAL."
                )
        
        # Regel 4: Transitions müssen gültige Ziele haben [WARNING]
        transitions = getattr(element, "state_transitions", [])
        for i, trans in enumerate(transitions):
            target = trans.get("target", "")
            if target:
                target_element = doc.get_element(target)
                if not target_element:
                    result.add_warning(
                        category="state",
                        message=f"Transition #{i+1} target '{target}' does not exist",
                        element_id=element.element_id,
                        suggestion="Select an existing STATE element as transition target"
                    )
                elif target_element.element_type != "STATE":
                    result.add_warning(
                        category="state",
                        message=f"Transition #{i+1} target '{target}' is not a STATE element",
                        element_id=element.element_id,
                        suggestion="Transitions should target other STATE elements"
                    )
        
        # Regel 5: Entry/Exit Actions sollten gültig sein [INFO]
        entry_action = getattr(element, "state_entry_action", "").strip()
        if entry_action:
            # Prüfe ob es ein Element-ID ist
            action_element = doc.get_element(entry_action)
            if action_element:
                result.add_info(
                    category="state",
                    message=f"Entry action references element '{entry_action}' ({action_element.element_type})",
                    element_id=element.element_id
                )
            else:
                # Annahme: Es ist ein Script/Expression
                result.add_info(
                    category="state",
                    message=f"Entry action uses script/expression: '{entry_action[:50]}{'...' if len(entry_action) > 50 else ''}'",
                    element_id=element.element_id
                )
        
        exit_action = getattr(element, "state_exit_action", "").strip()
        if exit_action:
            action_element = doc.get_element(exit_action)
            if action_element:
                result.add_info(
                    category="state",
                    message=f"Exit action references element '{exit_action}' ({action_element.element_type})",
                    element_id=element.element_id
                )
            else:
                result.add_info(
                    category="state",
                    message=f"Exit action uses script/expression: '{exit_action[:50]}{'...' if len(exit_action) > 50 else ''}'",
                    element_id=element.element_id
                )
        
        # Regel 6: Timeout-Target muss existieren wenn Timeout > 0 [WARNING]
        timeout = getattr(element, "state_timeout", 0)
        timeout_target = getattr(element, "state_timeout_target", "").strip()
        if timeout > 0:
            if not timeout_target:
                result.add_warning(
                    category="state",
                    message=f"Timeout is set ({timeout}s) but no timeout target defined",
                    element_id=element.element_id,
                    suggestion="Define a timeout target STATE or set timeout to 0"
                )
            else:
                target_element = doc.get_element(timeout_target)
                if not target_element:
                    result.add_warning(
                        category="state",
                        message=f"Timeout target '{timeout_target}' does not exist",
                        element_id=element.element_id,
                        suggestion="Select an existing STATE element as timeout target"
                    )
                elif target_element.element_type != "STATE":
                    result.add_warning(
                        category="state",
                        message=f"Timeout target '{timeout_target}' is not a STATE element",
                        element_id=element.element_id,
                        suggestion="Timeout should target a STATE element"
                    )
        
        # Regel 7: INITIAL-State sollte keine eingehenden Verbindungen haben [WARNING]
        if state_type == "INITIAL":
            incoming = doc.get_incoming_connections(element.element_id)
            if incoming:
                result.add_warning(
                    category="state",
                    message=f"INITIAL state has {len(incoming)} incoming connection(s)",
                    element_id=element.element_id,
                    suggestion="INITIAL states typically don't have incoming connections (entry point)"
                )
        
        # Regel 8: FINAL-State sollte keine ausgehenden Verbindungen haben [WARNING]
        if state_type == "FINAL":
            outgoing = doc.get_outgoing_connections(element.element_id)
            if outgoing:
                result.add_warning(
                    category="state",
                    message=f"FINAL state has {len(outgoing)} outgoing connection(s)",
                    element_id=element.element_id,
                    suggestion="FINAL states typically don't have outgoing connections (end point)"
                )
        
        # Regel 9: NORMAL/ERROR-States sollten Transitions haben [INFO]
        if state_type in ["NORMAL", "ERROR"] and not transitions:
            result.add_info(
                category="state",
                message=f"{state_type} state has no transitions defined",
                element_id=element.element_id,
                suggestion="Consider adding transitions to define state flow"
            )


class InterlockValidator:
    """Validiert INTERLOCK-Elemente (Mutex/Semaphore)."""
    
    VALID_TYPES = ["MUTEX", "SEMAPHORE"]
    
    def validate_interlock(self, element, doc, result):
        """
        Validiert ein INTERLOCK-Element.
        
        Args:
            element: Das zu validierende Element
            doc: Das VPBDocument
            result: ValidationResult zum Hinzufügen von Fehlern/Warnungen
        """
        # Regel 1: Resource-ID darf nicht leer sein [ERROR]
        resource_id = getattr(element, "interlock_resource_id", "").strip()
        if not resource_id:
            result.add_error(
                category="interlock",
                message="INTERLOCK element must have a resource ID",
                element_id=element.element_id,
                suggestion="Enter a unique resource identifier (e.g., 'db_conn', 'api_rate_limit', 'logfile')"
            )
        
        # Regel 2: Interlock-Type muss gültig sein [ERROR]
        interlock_type = getattr(element, "interlock_type", "MUTEX")
        if interlock_type not in self.VALID_TYPES:
            result.add_error(
                category="interlock",
                message=f"Invalid interlock type '{interlock_type}'",
                element_id=element.element_id,
                suggestion=f"Use one of: {', '.join(self.VALID_TYPES)}"
            )
        
        # Regel 3: Max-Count muss > 0 sein, besonders für SEMAPHORE [ERROR]
        max_count = getattr(element, "interlock_max_count", 1)
        if max_count <= 0:
            result.add_error(
                category="interlock",
                message=f"Max count must be > 0 (current: {max_count})",
                element_id=element.element_id,
                suggestion="MUTEX should have max_count=1, SEMAPHORE should have max_count>1"
            )
        
        # Regel 3b: SEMAPHORE sollte max_count > 1 haben [WARNING]
        if interlock_type == "SEMAPHORE" and max_count == 1:
            result.add_warning(
                category="interlock",
                message="SEMAPHORE with max_count=1 behaves like MUTEX",
                element_id=element.element_id,
                suggestion="Consider using MUTEX type or increase max_count for concurrent access"
            )
        
        # Regel 4: Timeout muss >= 0 sein [ERROR]
        timeout = getattr(element, "interlock_timeout", 0)
        if timeout < 0:
            result.add_error(
                category="interlock",
                message=f"Timeout cannot be negative (current: {timeout})",
                element_id=element.element_id,
                suggestion="Use 0 for indefinite wait, or a positive value for timeout in seconds"
            )
        
        # Regel 5: Locked-Target muss existieren wenn gesetzt [WARNING]
        locked_target = getattr(element, "interlock_on_locked_target", "").strip()
        if locked_target:
            target_element = doc.get_element(locked_target)
            if not target_element:
                result.add_warning(
                    category="interlock",
                    message=f"On-locked target '{locked_target}' does not exist",
                    element_id=element.element_id,
                    suggestion="Select an existing element as fallback when lock is unavailable"
                )
        
        # Regel 6: Resource-ID-Duplikate warnen [WARNING]
        if resource_id:
            interlocks_with_same_resource = [
                el for el in doc.get_all_elements()
                if el.element_type == "INTERLOCK" 
                and getattr(el, "interlock_resource_id", "") == resource_id
            ]
            if len(interlocks_with_same_resource) > 1:
                result.add_warning(
                    category="interlock",
                    message=f"Resource ID '{resource_id}' is used by {len(interlocks_with_same_resource)} INTERLOCK elements",
                    element_id=element.element_id,
                    suggestion="Multiple INTERLOCK elements with same resource ID can coordinate access"
                )
        
        # Regel 7: Timeout ohne Locked-Target ist problematisch [WARNING]
        if timeout > 0 and not locked_target:
            result.add_warning(
                category="interlock",
                message=f"Timeout is set ({timeout}s) but no fallback target defined",
                element_id=element.element_id,
                suggestion="Define an 'on-locked' target to handle timeout gracefully"
            )
        
        # Regel 8: Auto-Release ist Standard [INFO]
        auto_release = getattr(element, "interlock_auto_release", True)
        if not auto_release:
            result.add_info(
                category="interlock",
                message="Auto-release is disabled - manual release required",
                element_id=element.element_id,
                suggestion="Ensure explicit release logic exists to prevent deadlocks"
            )
        
        # Regel 9: MUTEX-Spezifische Prüfungen [INFO]
        if interlock_type == "MUTEX":
            if max_count != 1:
                result.add_info(
                    category="interlock",
                    message=f"MUTEX has max_count={max_count} (typically 1 for exclusive access)",
                    element_id=element.element_id,
                    suggestion="MUTEX is designed for max_count=1 (exclusive lock)"
                )


