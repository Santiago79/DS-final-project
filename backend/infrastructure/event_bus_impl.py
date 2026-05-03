"""
In-Memory Event Bus implementation.

Manages subscriptions and publication of domain events.
Implements the Observer pattern for decoupled event handling.
"""

from typing import Dict, List, Type

from domain.events import Evento
from domain.interfaces.event_bus import EventBus
from domain.interfaces.observador_evento import ObservadorEvento


class InMemoryEventBus(EventBus):
    """
    In-memory implementation of EventBus.
    
    Manages observers subscriptions and publishes events to all subscribed observers.
    This is a singleton pattern - only one instance should exist per application.
    """

    def __init__(self):
        """Initialize the event bus with empty subscriptions."""
        # Dictionary mapping event types to lists of observers
        self._subscriptions: Dict[Type[Evento], List[ObservadorEvento]] = {}

    def subscribe(self, observador: ObservadorEvento) -> None:
        """
        Subscribe an observer to all events.
        
        The observer will receive all published events through its on_event method.
        
        Args:
            observador: Observer implementing ObservadorEvento interface
        """
        # Get all event types from the observer's type hints (if available)
        # For now, we subscribe to all events by adding to a generic key
        # When publish is called, we pass the actual event type
        if type(observador) not in self._subscriptions:
            self._subscriptions[type(observador)] = []
        
        if observador not in self._subscriptions[type(observador)]:
            self._subscriptions[type(observador)].append(observador)

    def unsubscribe(self, observador: ObservadorEvento) -> None:
        """
        Unsubscribe an observer from the event bus.
        
        The observer will no longer receive events after unsubscribing.
        
        Args:
            observador: Observer implementing ObservadorEvento interface
        """
        observer_type = type(observador)
        if observer_type in self._subscriptions:
            self._subscriptions[observer_type] = [
                obs for obs in self._subscriptions[observer_type]
                if obs is not observador
            ]
            if not self._subscriptions[observer_type]:
                del self._subscriptions[observer_type]

    def publish(self, evento: Evento) -> None:
        """
        Publish an event to all subscribed observers.
        
        Iterates through all observers and calls their on_event method with the event.
        
        Args:
            evento: Event to publish
        """
        # Collect all observers from all subscriptions
        all_observers: List[ObservadorEvento] = []
        for observers in self._subscriptions.values():
            all_observers.extend(observers)
        
        # Notify each observer
        for observador in all_observers:
            try:
                observador.on_event(evento)
            except Exception as e:
                # Log error but don't stop other observers
                print(f"Error notifying observer {observador}: {str(e)}")

    def get_subscribers_count(self) -> int:
        """Get total number of subscribed observers (for testing/debugging)."""
        count = 0
        for observers in self._subscriptions.values():
            count += len(observers)
        return count
