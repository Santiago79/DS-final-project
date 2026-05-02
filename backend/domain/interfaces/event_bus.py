"""
Interfaz para el Event Bus (publicador de eventos).
Actúa como mediador entre productores y consumidores de eventos.
Implementa el patrón Observer en la capa de dominio.
"""

from abc import ABC, abstractmethod
from domain.events import Evento
from domain.interfaces.observador_evento import ObservadorEvento


class EventBus(ABC):
    """Interfaz para el bus de eventos del dominio."""

    @abstractmethod
    def subscribe(self, observador: ObservadorEvento) -> None:
        """
        Suscribe un observador para recibir eventos.

        Args:
            observador: El observador que se suscribe al bus
        """
        pass

    @abstractmethod
    def unsubscribe(self, observador: ObservadorEvento) -> None:
        """
        Desuscribe un observador para dejar de recibir eventos.

        Args:
            observador: El observador que se desuscribe del bus
        """
        pass

    @abstractmethod
    def publish(self, evento: Evento) -> None:
        """
        Publica un evento a todos los observadores suscritos.

        Args:
            evento: El evento a publicar
        """
        pass