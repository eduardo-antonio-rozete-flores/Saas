# application/controllers/inventory_controller.py
#
# NUEVA — Fase 5: Inventario Inteligente
#
# RESPONSABILIDAD:
#   Puente entre InventoryView e InventoryService.
#   Captura excepciones y las convierte en snackbars.
#   No contiene lógica de negocio.

class InventoryController:

    def __init__(self, service, app):
        self.service = service
        self.app     = app

    def get_inventory(self) -> list:
        try:
            return self.service.list_inventory()
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return []

    def get_low_stock_alerts(self) -> list:
        try:
            return self.service.get_low_stock_alerts()
        except Exception:
            return []

    def has_low_stock(self) -> bool:
        try:
            return self.service.has_low_stock()
        except Exception:
            return False

    def adjust_stock(self, product_id: str, nuevo_stock: int,
                     stock_minimo: int = None, notas: str = "") -> bool: #type: ignore
        try:
            self.service.adjust_stock(product_id, nuevo_stock, stock_minimo, notas)
            self.app.show_snackbar("Stock actualizado ✓")
            return True
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False

    def get_kardex(self, product_id: str, limit: int = 50) -> list:
        try:
            return self.service.get_kardex(product_id, limit)
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return []