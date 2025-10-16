"""Unit tests for the Event-Bus System"""

import pytest
from vpb.infrastructure.event_bus import EventBus, get_global_event_bus


class TestEventBus:
    """Test suite for EventBus class."""
    
    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish functionality."""
        bus = EventBus()
        received_data = []
        
        def handler(data):
            received_data.append(data)
        
        bus.subscribe('test.event', handler)
        bus.publish('test.event', 'hello')
        
        assert len(received_data) == 1
        assert received_data[0] == 'hello'
    
    def test_multiple_subscribers(self):
        """Test that multiple subscribers receive the same event."""
        bus = EventBus()
        results = []
        
        def handler1(data):
            results.append(('handler1', data))
        
        def handler2(data):
            results.append(('handler2', data))
        
        bus.subscribe('test.event', handler1)
        bus.subscribe('test.event', handler2)
        bus.publish('test.event', 'data')
        
        assert len(results) == 2
        assert ('handler1', 'data') in results
        assert ('handler2', 'data') in results
    
    def test_unsubscribe(self):
        """Test unsubscribing from events."""
        bus = EventBus()
        received = []
        
        def handler(data):
            received.append(data)
        
        bus.subscribe('test.event', handler)
        bus.publish('test.event', '1')
        
        result = bus.unsubscribe('test.event', handler)
        assert result is True
        
        bus.publish('test.event', '2')
        
        assert len(received) == 1
        assert received[0] == '1'
    
    def test_unsubscribe_nonexistent(self):
        """Test unsubscribing a callback that wasn't subscribed."""
        bus = EventBus()
        
        def handler(data):
            pass
        
        result = bus.unsubscribe('nonexistent.event', handler)
        assert result is False
    
    def test_publish_without_subscribers(self):
        """Test publishing to an event with no subscribers."""
        bus = EventBus()
        count = bus.publish('lonely.event', 'data')
        assert count == 0
    
    def test_error_handling_in_callback(self):
        """Test that errors in callbacks don't crash the bus."""
        bus = EventBus()
        results = []
        
        def bad_handler(data):
            raise ValueError("Intentional error")
        
        def good_handler(data):
            results.append(data)
        
        bus.subscribe('test.event', bad_handler)
        bus.subscribe('test.event', good_handler)
        
        count = bus.publish('test.event', 'data')
        
        # Good handler should still execute
        assert len(results) == 1
        assert results[0] == 'data'
        # Only 1 success despite 2 subscribers
        assert count == 1
    
    def test_has_subscribers(self):
        """Test checking if an event has subscribers."""
        bus = EventBus()
        
        def handler(data):
            pass
        
        assert bus.has_subscribers('test.event') is False
        
        bus.subscribe('test.event', handler)
        assert bus.has_subscribers('test.event') is True
        
        bus.unsubscribe('test.event', handler)
        assert bus.has_subscribers('test.event') is False
    
    def test_get_subscriber_count(self):
        """Test getting subscriber count."""
        bus = EventBus()
        
        def handler1(data):
            pass
        
        def handler2(data):
            pass
        
        assert bus.get_subscriber_count('test.event') == 0
        
        bus.subscribe('test.event', handler1)
        assert bus.get_subscriber_count('test.event') == 1
        
        bus.subscribe('test.event', handler2)
        assert bus.get_subscriber_count('test.event') == 2
    
    def test_clear_subscribers(self):
        """Test clearing subscribers."""
        bus = EventBus()
        
        def handler(data):
            pass
        
        bus.subscribe('event1', handler)
        bus.subscribe('event2', handler)
        
        assert bus.get_subscriber_count('event1') == 1
        assert bus.get_subscriber_count('event2') == 1
        
        # Clear specific event
        bus.clear_subscribers('event1')
        assert bus.get_subscriber_count('event1') == 0
        assert bus.get_subscriber_count('event2') == 1
        
        # Clear all
        bus.clear_subscribers()
        assert bus.get_subscriber_count('event2') == 0
    
    def test_enable_disable(self):
        """Test enabling/disabling the event bus."""
        bus = EventBus()
        results = []
        
        def handler(data):
            results.append(data)
        
        bus.subscribe('test.event', handler)
        
        # Publish while enabled
        bus.enable()
        bus.publish('test.event', '1')
        assert len(results) == 1
        
        # Publish while disabled
        bus.disable()
        bus.publish('test.event', '2')
        assert len(results) == 1  # Still 1, not 2
        
        # Re-enable
        bus.enable()
        bus.publish('test.event', '3')
        assert len(results) == 2
    
    def test_get_all_events(self):
        """Test getting all registered events."""
        bus = EventBus()
        
        def handler(data):
            pass
        
        bus.subscribe('event1', handler)
        bus.subscribe('event2', handler)
        bus.subscribe('event3', handler)
        
        events = bus.get_all_events()
        assert len(events) == 3
        assert 'event1' in events
        assert 'event2' in events
        assert 'event3' in events
    
    def test_event_history(self):
        """Test event history tracking."""
        bus = EventBus()
        
        bus.publish('event1', 'data1')
        bus.publish('event2', 'data2')
        bus.publish('event3', 'data3')
        
        history = bus.get_event_history()
        assert len(history) == 3
        assert history[0] == ('event1', 'data1')
        assert history[1] == ('event2', 'data2')
        assert history[2] == ('event3', 'data3')
        
        # Test limit
        limited = bus.get_event_history(limit=2)
        assert len(limited) == 2
        assert limited[0] == ('event2', 'data2')
    
    def test_duplicate_subscription(self):
        """Test that subscribing the same callback twice doesn't duplicate it."""
        bus = EventBus()
        results = []
        
        def handler(data):
            results.append(data)
        
        bus.subscribe('test.event', handler)
        bus.subscribe('test.event', handler)  # Duplicate
        
        bus.publish('test.event', 'data')
        
        # Should only be called once
        assert len(results) == 1
    
    def test_repr(self):
        """Test string representation."""
        bus = EventBus()
        
        def handler(data):
            pass
        
        bus.subscribe('event1', handler)
        bus.subscribe('event2', handler)
        
        repr_str = repr(bus)
        assert 'EventBus' in repr_str
        assert '2 events' in repr_str
        assert 'enabled' in repr_str


class TestGlobalEventBus:
    """Test suite for global event bus singleton."""
    
    def test_global_singleton(self):
        """Test that global event bus returns the same instance."""
        bus1 = get_global_event_bus()
        bus2 = get_global_event_bus()
        
        assert bus1 is bus2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
