# application/controllers/product_controller.py
#
# CAMBIOS (Fase 4 — Código de Barras):
#
# 1. find_by_barcode(barcode) — delega a ProductService.find_by_barcode().
#    Llamado desde PosView cuando el cajero escanea un código.
#
# 2. generate_barcode(product_id) — helper para asignar barcode automático
#    desde ProductsView al editar un producto sin barcode.

class ProductController:

    def __init__(self, service, app):
        self.service = service
        self.app     = app

    def get_products(self):
        try:
            return self.service.list_products()
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return []

    def search_products(self, query: str):
        try:
            return self.service.search_products(query)
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return []

    # ------------------------------------------------------------------ #
    # NUEVO Fase 4                                                        #
    # ------------------------------------------------------------------ #
    def find_by_barcode(self, barcode: str) -> dict | None:
        """
        Busca un producto por barcode exacto.
        Devuelve None (sin snackbar) si no se encuentra — la vista decide
        cómo informarlo (beep, shake, mensaje inline).
        """
        try:
            return self.service.find_by_barcode(barcode)
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return None

    def generate_barcode(self, product_id: str) -> str:
        """Genera y devuelve un barcode numérico para el producto."""
        try:
            return self.service.generate_barcode_for(product_id)
        except Exception:
            return ""

    # ------------------------------------------------------------------ #
    # CRUD                                                                #
    # ------------------------------------------------------------------ #
    def create_product(self, data: dict) -> bool:
        try:
            self.service.create_product(data)
            self.app.show_snackbar("Producto creado exitosamente ✓")
            return True
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False

    def update_product(self, product_id: str, data: dict) -> bool:
        try:
            self.service.update_product(product_id, data)
            self.app.show_snackbar("Producto actualizado ✓")
            return True
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False

    def delete_product(self, product_id: str) -> bool:
        try:
            self.service.delete_product(product_id)
            self.app.show_snackbar("Producto eliminado")
            return True
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False

    def get_count(self) -> int:
        try:
            return self.service.get_count()
        except Exception:
            return 0