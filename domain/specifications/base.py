# domain/specifications/base.py
#
# Patrón Specification (DDD).
#
# PROPÓSITO:
#   Encapsular una regla de negocio en un objeto con nombre explícito.
#   Las specs se pueden combinar con and_/or_/not_ para crear reglas complejas
#   sin proliferar condicionales en los servicios.
#
# EJEMPLO DE USO:
#   low  = LowStockSpec()
#   out  = OutOfStockSpec()
#
#   # Productos agotados O con stock bajo:
#   critical = out.or_(low)
#   critical_items = critical.filter(inventory_list)
#
#   # Productos con stock bajo pero aún no agotados:
#   low_not_zero = low.and_(out.not_())
#   items = low_not_zero.filter(inventory_list)

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """Clase base abstracta para el patrón Specification."""

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Retorna True si el candidato satisface la especificación."""
        ...

    # ─── Operadores de composición ────────────────────────────────

    def and_(self, other: "Specification[T]") -> "AndSpecification[T]":
        """Composición AND: ambas specs deben cumplirse."""
        return AndSpecification(self, other)

    def or_(self, other: "Specification[T]") -> "OrSpecification[T]":
        """Composición OR: al menos una spec debe cumplirse."""
        return OrSpecification(self, other)

    def not_(self) -> "NotSpecification[T]":
        """Negación: la spec NO debe cumplirse."""
        return NotSpecification(self)

    # ─── Helper de filtrado ───────────────────────────────────────

    def filter(self, candidates: List[T]) -> List[T]:
        """Filtra una lista retornando solo los candidatos que satisfacen la spec."""
        return [c for c in candidates if self.is_satisfied_by(c)]

    def count(self, candidates: List[T]) -> int:
        """Cuenta cuántos candidatos satisfacen la spec."""
        return sum(1 for c in candidates if self.is_satisfied_by(c))


class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self._left  = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (self._left.is_satisfied_by(candidate)
                and self._right.is_satisfied_by(candidate))


class OrSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]):
        self._left  = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return (self._left.is_satisfied_by(candidate)
                or self._right.is_satisfied_by(candidate))


class NotSpecification(Specification[T]):
    def __init__(self, spec: Specification[T]):
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self._spec.is_satisfied_by(candidate)
