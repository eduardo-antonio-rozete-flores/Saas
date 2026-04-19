# application/controllers/product_controller.py
#
# CAMBIOS (refactor arquitectural):
#   • Maneja excepciones de dominio específicas:
#       ValidationError  → el usuario cometió un error de entrada
#       NexaPOSError     → error de dominio conocido
#       Exception        → error inesperado del sistema (mensaje genérico)
#   • La firma pública es idéntica — las vistas no cambian.
#
# FASE 4 (Código de Barras) conservada.
#
# CAMBIO (Stock inicial):
#   • __init__ acepta create_product_use_case opcional.
#   • create_product() usa el use case si está disponible; fallback a service.
#     El use case es el que llama a inventory_service.initialize_stock().

from domain.exceptions import ValidationError, NexaPOSError


class ProductController:

    def __init__(self, service, app, create_product_use_case=None):
        self.service          = service
        self.app              = app
        self._create_use_case = create_product_use_case

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

    # ─── Fase 4 ───────────────────────────────────────────────────

    def find_by_barcode(self, barcode: str) -> dict | None:
        try:
            return self.service.find_by_barcode(barcode)
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return None

    def generate_barcode(self, product_id: str) -> str:
        try:
            return self.service.generate_barcode_for(product_id)
        except Exception:
            return ""

    # ─── CRUD ─────────────────────────────────────────────────────

    def create_product(self, data: dict) -> bool:
        try:
            if self._create_use_case:
                self._create_use_case.execute(data)
            else:
                self.service.create_product(data)
            self.app.show_snackbar("Producto creado exitosamente ✓")
            return True
        except ValidationError as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False
        except NexaPOSError as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False
        except Exception as ex:
            self.app.show_snackbar(f"Error inesperado: {ex}", error=True)
            return False

    def update_product(self, product_id: str, data: dict) -> bool:
        try:
            self.service.update_product(product_id, data)
            self.app.show_snackbar("Producto actualizado ✓")
            return True
        except ValidationError as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False
        except NexaPOSError as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False
        except Exception as ex:
            self.app.show_snackbar(f"Error inesperado: {ex}", error=True)
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
