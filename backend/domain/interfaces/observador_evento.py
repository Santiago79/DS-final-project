"""
Interfaz base para observadores de eventos del dominio.
Implementa el patrón Observer para reaccionar a eventos del sistema.
"""

from abc import ABC, abstractmethod
from domain.events import Evento


class ObservadorEvento(ABC):
    """Interfaz base para observadores de eventos del dominio."""

    @abstractmethod
    def on_event(self, evento: Evento) -> None:
        """
        Procesa un evento cuando es publicado.

        Args:
            evento: El evento que ocurrió en el dominio
        """
        pass