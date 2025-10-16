"""
VPB Event-Bus - Usage Examples
================================

This document shows how to use the EventBus system in VPB Process Designer.
"""

from vpb.infrastructure.event_bus import EventBus, get_global_event_bus


# ============================================================================
# Example 1: Basic Usage
# ============================================================================

def example_basic():
    """Simple subscribe and publish."""
    bus = EventBus()
    
    # Define handler
    def on_file_opened(data):
        print(f"File opened: {data['path']}")
    
    # Subscribe
    bus.subscribe('file.opened', on_file_opened)
    
    # Publish
    bus.publish('file.opened', {'path': 'example.vpb'})
    # Output: File opened: example.vpb


# ============================================================================
# Example 2: Multiple Subscribers
# ============================================================================

def example_multiple_subscribers():
    """Multiple components listening to the same event."""
    bus = EventBus()
    
    # UI updates
    def update_status_bar(data):
        print(f"Status: Document saved to {data['path']}")
    
    # Telemetry tracking
    def log_to_telemetry(data):
        print(f"Telemetry: Document saved at {data['timestamp']}")
    
    # Recent files list
    def add_to_recent(data):
        print(f"Recent: Adding {data['path']}")
    
    # All subscribe to same event
    bus.subscribe('document.saved', update_status_bar)
    bus.subscribe('document.saved', log_to_telemetry)
    bus.subscribe('document.saved', add_to_recent)
    
    # Single publish triggers all
    bus.publish('document.saved', {
        'path': 'my_process.vpb',
        'timestamp': '2025-01-14T10:30:00'
    })


# ============================================================================
# Example 3: View → Controller → Service Communication
# ============================================================================

class SimpleView:
    """Example view that publishes user actions."""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
    
    def on_save_button_clicked(self):
        """User clicked Save button."""
        print("[View] Save button clicked")
        self.event_bus.publish('ui.save_requested')


class SimpleController:
    """Example controller that handles events."""
    
    def __init__(self, event_bus, service):
        self.event_bus = event_bus
        self.service = service
        
        # Subscribe to events
        self.event_bus.subscribe('ui.save_requested', self.handle_save)
    
    def handle_save(self, data):
        """Handle save request from UI."""
        print("[Controller] Handling save request")
        result = self.service.save_document()
        
        # Notify UI of result
        if result:
            self.event_bus.publish('document.saved', {'success': True})
        else:
            self.event_bus.publish('document.save_failed', {'error': 'Disk full'})


class SimpleService:
    """Example service that performs operations."""
    
    def save_document(self):
        """Business logic for saving."""
        print("[Service] Saving document...")
        return True


def example_mvc():
    """Full MVC flow with event bus."""
    bus = EventBus()
    
    service = SimpleService()
    controller = SimpleController(bus, service)
    view = SimpleView(bus)
    
    # Also let view react to results
    def on_save_success(data):
        print("[View] ✓ Document saved successfully!")
    
    bus.subscribe('document.saved', on_save_success)
    
    # User action triggers the flow
    view.on_save_button_clicked()
    # Output:
    # [View] Save button clicked
    # [Controller] Handling save request
    # [Service] Saving document...
    # [View] ✓ Document saved successfully!


# ============================================================================
# Example 4: Error Handling
# ============================================================================

def example_error_handling():
    """Demonstrate robust error handling."""
    bus = EventBus()
    
    def buggy_handler(data):
        raise ValueError("Oops, this handler has a bug!")
    
    def good_handler(data):
        print("Good handler executed successfully")
    
    bus.subscribe('test.event', buggy_handler)
    bus.subscribe('test.event', good_handler)
    
    # Even with buggy handler, good handler still executes
    success_count = bus.publish('test.event')
    print(f"Successfully notified: {success_count} handlers")
    # Output: 
    # Good handler executed successfully
    # Successfully notified: 1 handlers


# ============================================================================
# Example 5: Global Event Bus (Simple Apps)
# ============================================================================

def example_global_bus():
    """Using the global singleton for simple apps."""
    
    # Get global instance (same everywhere)
    bus = get_global_event_bus()
    
    def handler(data):
        print(f"Global handler: {data}")
    
    bus.subscribe('app.initialized', handler)
    bus.publish('app.initialized', 'Ready!')


# ============================================================================
# Example 6: Temporary Subscriptions
# ============================================================================

def example_temporary_subscription():
    """Subscribe for a limited time."""
    bus = EventBus()
    
    def temporary_handler(data):
        print(f"Temporary: {data}")
    
    # Subscribe
    bus.subscribe('temp.event', temporary_handler)
    bus.publish('temp.event', 'Message 1')
    
    # Unsubscribe
    bus.unsubscribe('temp.event', temporary_handler)
    bus.publish('temp.event', 'Message 2')  # Won't be received


# ============================================================================
# Example 7: Event Categories (Recommended Pattern)
# ============================================================================

# Recommended event naming conventions:

EVENTS = {
    # File operations
    'FILE_NEW': 'file.new',
    'FILE_OPEN': 'file.open',
    'FILE_SAVE': 'file.save',
    'FILE_SAVE_AS': 'file.save_as',
    'FILE_CLOSE': 'file.close',
    
    # Document changes
    'DOCUMENT_LOADED': 'document.loaded',
    'DOCUMENT_SAVED': 'document.saved',
    'DOCUMENT_MODIFIED': 'document.modified',
    
    # Element operations
    'ELEMENT_ADDED': 'element.added',
    'ELEMENT_DELETED': 'element.deleted',
    'ELEMENT_MODIFIED': 'element.modified',
    'ELEMENT_SELECTED': 'element.selected',
    
    # Canvas operations
    'CANVAS_REFRESH': 'canvas.refresh',
    'CANVAS_ZOOM': 'canvas.zoom',
    'CANVAS_PAN': 'canvas.pan',
    
    # UI operations
    'UI_STATUS_UPDATE': 'ui.status_update',
    'UI_ERROR': 'ui.error',
    'UI_PROGRESS': 'ui.progress',
}

def example_event_categories():
    """Using event constants for type safety."""
    bus = EventBus()
    
    def on_element_added(data):
        print(f"Element added: {data['element_type']}")
    
    # Use constant instead of string
    bus.subscribe(EVENTS['ELEMENT_ADDED'], on_element_added)
    bus.publish(EVENTS['ELEMENT_ADDED'], {'element_type': 'VorProzess'})


# ============================================================================
# Run Examples
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("Example 1: Basic Usage")
    print("=" * 70)
    example_basic()
    
    print("\n" + "=" * 70)
    print("Example 2: Multiple Subscribers")
    print("=" * 70)
    example_multiple_subscribers()
    
    print("\n" + "=" * 70)
    print("Example 3: MVC Flow")
    print("=" * 70)
    example_mvc()
    
    print("\n" + "=" * 70)
    print("Example 4: Error Handling")
    print("=" * 70)
    example_error_handling()
    
    print("\n" + "=" * 70)
    print("Example 5: Global Bus")
    print("=" * 70)
    example_global_bus()
    
    print("\n" + "=" * 70)
    print("Example 6: Temporary Subscription")
    print("=" * 70)
    example_temporary_subscription()
    
    print("\n" + "=" * 70)
    print("Example 7: Event Categories")
    print("=" * 70)
    example_event_categories()
