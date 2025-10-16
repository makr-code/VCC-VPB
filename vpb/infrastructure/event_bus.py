"""
Event-Bus System for VPB Process Designer
==========================================

Implements a centralized event-driven architecture for loose coupling
between components (Views, Controllers, Services).

Example Usage:
    ```python
    event_bus = EventBus()
    
    # Subscribe to events
    def on_document_saved(data):
        print(f"Document saved: {data}")
    
    event_bus.subscribe('document.saved', on_document_saved)
    
    # Publish events
    event_bus.publish('document.saved', {'path': 'example.vpb'})
    
    # Unsubscribe
    event_bus.unsubscribe('document.saved', on_document_saved)
    ```

Event Naming Convention:
    - Use dot notation: 'category.action'
    - Examples: 'file.open', 'element.added', 'canvas.refresh'
"""

from typing import Callable, Dict, List, Any, Optional
import logging
import traceback


logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event dispatcher for decoupled communication.
    
    Attributes:
        _subscribers: Dictionary mapping event names to callback lists
        _enabled: Whether event dispatching is enabled
    """
    
    def __init__(self):
        """Initialize an empty event bus."""
        self._subscribers: Dict[str, List[Callable]] = {}
        self._enabled: bool = True
        self._event_history: List[tuple] = []  # For debugging
        self._max_history: int = 100
        
    def subscribe(self, event: str, callback: Callable[[Any], None]) -> None:
        """
        Register a callback function for a specific event.
        
        Args:
            event: Event name (e.g., 'file.open')
            callback: Function to call when event is published.
                     Should accept a single data parameter.
        
        Example:
            >>> def handler(data):
            ...     print(f"Received: {data}")
            >>> bus = EventBus()
            >>> bus.subscribe('test.event', handler)
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        
        if callback not in self._subscribers[event]:
            self._subscribers[event].append(callback)
            logger.debug(f"Subscribed to '{event}': {callback.__name__}")
        else:
            logger.warning(f"Callback {callback.__name__} already subscribed to '{event}'")
    
    def unsubscribe(self, event: str, callback: Callable[[Any], None]) -> bool:
        """
        Remove a callback function from an event.
        
        Args:
            event: Event name
            callback: Previously registered callback
            
        Returns:
            True if callback was found and removed, False otherwise
        
        Example:
            >>> bus.unsubscribe('test.event', handler)
            True
        """
        if event in self._subscribers:
            try:
                self._subscribers[event].remove(callback)
                logger.debug(f"Unsubscribed from '{event}': {callback.__name__}")
                
                # Clean up empty subscriber lists
                if not self._subscribers[event]:
                    del self._subscribers[event]
                
                return True
            except ValueError:
                logger.warning(f"Callback {callback.__name__} not found for '{event}'")
                return False
        
        return False
    
    def publish(self, event: str, data: Any = None) -> int:
        """
        Fire an event and notify all subscribers.
        
        Args:
            event: Event name to publish
            data: Optional data to pass to callbacks
            
        Returns:
            Number of callbacks that were successfully notified
        
        Example:
            >>> bus.publish('file.opened', {'path': 'document.vpb'})
            2  # 2 callbacks were notified
        """
        if not self._enabled:
            logger.debug(f"Event bus disabled, ignoring event: {event}")
            return 0
        
        # Record in history (for debugging)
        self._event_history.append((event, data))
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        success_count = 0
        
        if event in self._subscribers:
            logger.debug(f"Publishing '{event}' to {len(self._subscribers[event])} subscribers")
            
            for callback in self._subscribers[event][:]:  # Copy list to allow modifications
                try:
                    callback(data)
                    success_count += 1
                except Exception as e:
                    logger.error(
                        f"Error in event handler for '{event}': {callback.__name__}\n"
                        f"Error: {e}\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
        else:
            logger.debug(f"No subscribers for event: {event}")
        
        return success_count
    
    def has_subscribers(self, event: str) -> bool:
        """
        Check if an event has any subscribers.
        
        Args:
            event: Event name
            
        Returns:
            True if event has at least one subscriber
        """
        return event in self._subscribers and len(self._subscribers[event]) > 0
    
    def get_subscriber_count(self, event: str) -> int:
        """
        Get number of subscribers for an event.
        
        Args:
            event: Event name
            
        Returns:
            Number of subscribers
        """
        return len(self._subscribers.get(event, []))
    
    def clear_subscribers(self, event: Optional[str] = None) -> None:
        """
        Remove all subscribers from an event, or all events.
        
        Args:
            event: Specific event to clear, or None to clear all
        """
        if event:
            if event in self._subscribers:
                del self._subscribers[event]
                logger.debug(f"Cleared all subscribers for '{event}'")
        else:
            self._subscribers.clear()
            logger.debug("Cleared all event subscribers")
    
    def enable(self) -> None:
        """Enable event dispatching."""
        self._enabled = True
        logger.debug("Event bus enabled")
    
    def disable(self) -> None:
        """Disable event dispatching (for testing/debugging)."""
        self._enabled = False
        logger.debug("Event bus disabled")
    
    def get_all_events(self) -> List[str]:
        """
        Get list of all events that have subscribers.
        
        Returns:
            List of event names
        """
        return list(self._subscribers.keys())
    
    def get_event_history(self, limit: Optional[int] = None) -> List[tuple]:
        """
        Get recent event history (for debugging).
        
        Args:
            limit: Maximum number of events to return (None = all)
            
        Returns:
            List of (event_name, data) tuples
        """
        if limit:
            return self._event_history[-limit:]
        return self._event_history.copy()
    
    def __repr__(self) -> str:
        """String representation of the event bus."""
        event_count = len(self._subscribers)
        total_subscribers = sum(len(subs) for subs in self._subscribers.values())
        return (
            f"<EventBus: {event_count} events, "
            f"{total_subscribers} total subscribers, "
            f"{'enabled' if self._enabled else 'disabled'}>"
        )


# Global singleton instance (optional convenience)
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """
    Get or create a global EventBus singleton.
    
    Useful for simple applications that only need one event bus.
    For more complex apps, create separate EventBus instances.
    
    Returns:
        Global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus
