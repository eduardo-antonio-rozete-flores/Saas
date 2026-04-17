# domain/specifications/low_stock_spec.py
#
# Especificaciones de inventario.
#
# InventoryService.get_low_stock_alerts() ya usa una RPC de Supabase, pero
# estas specs permiten aplicar la misma lógica localmente (sin DB) para:
#   • Filtrar listas en memoria antes de mostrarlas
#   • Tests unitarios sin mock de DB
#   • Lógica de clasificación en la vista (crítico vs precaución)

from domain.specifications.base import Specification


class LowStockSpec(Specification):
    """
    Satisfecha cuando stock_actual <= stock_minimo * factor.

    factor=1.0 (defecto): stock en o bajo el mínimo → alerta roja.
    factor=2.0:            stock bajo pero sobre el mínimo → alerta amarilla.
    """

    def __init__(self, threshold_factor: float = 1.0):
        self._factor = threshold_factor

    def is_satisfied_by(self, inventory_item: dict) -> bool:
        actual = inventory_item.get("stock_actual", 0)
        minimo = inventory_item.get("stock_minimo", 5)
        return actual <= (minimo * self._factor)


class OutOfStockSpec(Specification):
    """Satisfecha cuando stock_actual == 0 (producto agotado)."""

    def is_satisfied_by(self, inventory_item: dict) -> bool:
        return inventory_item.get("stock_actual", 0) == 0


class HealthyStockSpec(Specification):
    """
    Satisfecha cuando stock_actual > stock_minimo * 2.
    Útil para filtrar productos que NO necesitan atención.
    """

    def is_satisfied_by(self, inventory_item: dict) -> bool:
        actual = inventory_item.get("stock_actual", 0)
        minimo = inventory_item.get("stock_minimo", 5)
        return actual > minimo * 2
