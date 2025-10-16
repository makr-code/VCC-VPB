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
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ValidationService(naming={self.check_naming}, "
            f"flow={self.check_flow}, completeness={self.check_completeness})"
        )
