"""
Implementación del patrón Template Method para la verificación
de expiración de accesos.

La clase base define el algoritmo fijo de verificación y las subclases
concretas definen las variaciones según el nivel de acceso.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from domain.enums import AccessLevel

if TYPE_CHECKING:
    from domain.entities import AccessRequest


# ============================================================
# Value Object: Resultado de la verificación
# ============================================================

@dataclass(frozen=True)
class ExpirationResult:
    """Resultado inmutable de la verificación de expiración."""
    status: str            # NO_EXPIRATION, ACTIVE, EXPIRING_SOON, EXPIRED
    days_remaining: int
    severity: str          # INFO, WARNING, CRITICAL
    message: str
    requires_notification: bool = False


# ============================================================
# Template Method Base
# ============================================================

class ExpirationChecker(ABC):
    """
    Clase base abstracta que implementa el patrón Template Method.
    Define el algoritmo fijo para verificar la expiración de un acceso
    y deja que las subclases implementen los pasos que varían.
    """

    def check(self, request: "AccessRequest") -> ExpirationResult:
        """
        Método template que define el algoritmo de verificación.
        Las subclases NO deben sobrescribir este método.

        Args:
            request: La solicitud de acceso a verificar

        Returns:
            ExpirationResult con el estado, días restantes, severidad y mensaje
        """
        # Paso 1: ¿Tiene fecha de expiración?
        if not self._has_expiration(request):
            return ExpirationResult(
                status="NO_EXPIRATION",
                days_remaining=0,
                severity="INFO",
                message="Sin fecha de expiración configurada.",
                requires_notification=False,
            )

        # Paso 2: Calcular días restantes
        days_remaining = self._calculate_days_remaining(request)

        # Paso 3: ¿Ya expiró?
        if self._is_expired(days_remaining):
            return self._handle_expired(request, days_remaining)

        # Paso 4: ¿Está por expirar pronto?
        if self._is_expiring_soon(days_remaining):
            return self._handle_expiring_soon(request, days_remaining)

        # Paso 5: Todo en orden
        return self._handle_active(request, days_remaining)

    # ============================================================
    # Pasos que varían según el nivel de acceso
    # ============================================================

    @abstractmethod
    def _has_expiration(self, request: "AccessRequest") -> bool:
        """
        Determina si la solicitud tiene una fecha de expiración válida.
        ADMIN: obligatorio → True
        READ/WRITE: opcional → depende de si tiene fecha
        """
        pass

    def _calculate_days_remaining(self, request: "AccessRequest") -> int:
        """
        Calcula los días restantes hasta la expiración.
        Este paso es IGUAL para todos los niveles.
        Retorno negativo = ya expiró.
        """
        expiration = request.expiration_date
        today = date.today()
        delta = expiration - today
        return delta.days

    def _is_expired(self, days_remaining: int) -> bool:
        """
        Determina si el acceso ya expiró.
        IGUAL para todos: días negativos = expirado.
        """
        return days_remaining < 0

    @abstractmethod
    def _is_expiring_soon(self, days_remaining: int) -> bool:
        """
        Determina si está en el umbral de "por expirar pronto".
        ADMIN: 7 días
        READ/WRITE: 3 días
        """
        pass

    # ============================================================
    # Manejadores de resultado (varían por nivel)
    # ============================================================

    def _handle_active(self, request: "AccessRequest", days_remaining: int) -> ExpirationResult:
        """Acceso activo, no requiere acción."""
        return ExpirationResult(
            status="ACTIVE",
            days_remaining=days_remaining,
            severity="INFO",
            message=f"Acceso activo. Expira en {days_remaining} días.",
            requires_notification=False,
        )

    @abstractmethod
    def _handle_expired(self, request: "AccessRequest", days_remaining: int) -> ExpirationResult:
        """Maneja el caso de acceso expirado."""
        pass

    @abstractmethod
    def _handle_expiring_soon(self, request: "AccessRequest", days_remaining: int) -> ExpirationResult:
        """Maneja el caso de acceso próximo a expirar."""
        pass


# ============================================================
# Subclases Concretas
# ============================================================

class AdminExpirationChecker(ExpirationChecker):
    """
    Verificador de expiración para accesos ADMIN.
    
    Reglas específicas:
    - Expiración SIEMPRE obligatoria
    - Umbral de aviso: 7 días
    - Severidad CRITICAL si expira
    """

    def _has_expiration(self, request: "AccessRequest") -> bool:
        """ADMIN siempre debe tener fecha de expiración."""
        return request.expiration_date is not None

    def _is_expiring_soon(self, days_remaining: int) -> bool:
        """ADMIN: notificar con 7 días de anticipación."""
        return days_remaining <= 7

    def _handle_expired(self, request: "AccessRequest", days_remaining: int) -> ExpirationResult:
        """Acceso ADMIN expirado: CRÍTICO."""
        return ExpirationResult(
            status="EXPIRED",
            days_remaining=abs(days_remaining),
            severity="CRITICAL",
            message=(
                f"ACCESO ADMIN VENCIDO: {request.target_system} "
                f"expirado hace {abs(days_remaining)} días. "
                f"Se requiere revisión inmediata de Security."
            ),
            requires_notification=True,
        )

    def _handle_expiring_soon(self, request: "AccessRequest", days_remaining: int) -> ExpirationResult:
        """ADMIN por expirar: WARNING alto."""
        return ExpirationResult(
            status="EXPIRING_SOON",
            days_remaining=days_remaining,
            severity="WARNING",
            message=(
                f"ACCESO ADMIN PRÓXIMO A EXPIRAR: {request.target_system} "
                f"expira en {days_remaining} días. "
                f"Renueve o revoque el acceso antes de la fecha límite."
            ),
            requires_notification=True,
        )


class StandardExpirationChecker(ExpirationChecker):
    """
    Verificador de expiración para accesos READ y WRITE.
    
    Reglas específicas:
    - Expiración OPCIONAL
    - Umbral de aviso: 3 días
    - Severidad WARNING si expira
    """

    def _has_expiration(self, request: "AccessRequest") -> bool:
        """READ/WRITE: la expiración es opcional."""
        return request.expiration_date is not None

    def _is_expiring_soon(self, days_remaining: int) -> bool:
        """READ/WRITE: notificar con 3 días de anticipación."""
        return days_remaining <= 3

    def _handle_expired(self, request: "AccessRequest", days_remaining: int) -> ExpirationResult:
        """Acceso estándar expirado: WARNING normal."""
        return ExpirationResult(
            status="EXPIRED",
            days_remaining=abs(days_remaining),
            severity="WARNING",
            message=(
                f"Acceso a {request.target_system} expirado hace "
                f"{abs(days_remaining)} días. "
                f"Cree una nueva solicitud si aún lo necesita."
            ),
            requires_notification=True,
        )

    def _handle_expiring_soon(self, request: "AccessRequest", days_remaining: int) -> ExpirationResult:
        """Acceso estándar por expirar: INFO con aviso simple."""
        return ExpirationResult(
            status="EXPIRING_SOON",
            days_remaining=days_remaining,
            severity="INFO",
            message=(
                f"Tu acceso a {request.target_system} expirará en "
                f"{days_remaining} días. Solicita renovación si lo necesitas."
            ),
            requires_notification=True,
        )


# ============================================================
# Factory para seleccionar el checker correcto
# ============================================================

def get_expiration_checker(request: "AccessRequest") -> ExpirationChecker:
    """
    Selecciona el ExpirationChecker adecuado según el nivel de acceso.

    Args:
        request: La solicitud de acceso

    Returns:
        ExpirationChecker correspondiente al nivel
    """
    if request.access_level == AccessLevel.ADMIN:
        return AdminExpirationChecker()
    return StandardExpirationChecker()