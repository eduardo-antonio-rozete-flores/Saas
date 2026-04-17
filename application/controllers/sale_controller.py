# application/controllers/sale_controller.py
#
# CAMBIOS (refactor arquitectural):
#   • create_sale() usa CreateSaleUseCase cuando está inyectado (preferido).
#     Fallback a SaleService.create_sale() si el use case no está disponible.
#   • Maneja excepciones de dominio específicas:
#       ValidationError / BusinessRuleError → error de entrada o regla violada
#       NexaPOSError                        → cualquier error de dominio
#       Exception                           → error inesperado del sistema
#   • Las operaciones de lectura (get_sales, get_today_stats) siguen
#     usando SaleService directamente — no necesitan use case.

from domain.exceptions import ValidationError, BusinessRuleError, NexaPOSError
from domain.schemas.sale_schemas import CreateSaleRequest


class SaleController:

    def __init__(self, service, app, create_sale_use_case=None):
        self.service              = service
        self.app                  = app
        self._create_use_case     = create_sale_use_case

    def create_sale(self, cart: list, payment_method: str,
                    amount_received: float = 0) -> dict | None:
        try:
            if self._create_use_case:
                request = CreateSaleRequest.from_cart(
                    cart, payment_method, amount_received
                )
                result = self._create_use_case.execute(request)
            else:
                result = self.service.create_sale(cart, payment_method, amount_received)

            self.app.show_snackbar("¡Venta registrada exitosamente! ✓")
            return result

        except (ValidationError, BusinessRuleError) as ex:
            # Error de validación o regla de negocio: mostrar directo al usuario
            self.app.show_snackbar(str(ex), error=True)
            return None
        except NexaPOSError as ex:
            # Otro error de dominio conocido (RepositoryError, AuthenticationError…)
            self.app.show_snackbar(str(ex), error=True)
            return None
        except Exception as ex:
            self.app.show_snackbar(f"Error inesperado al registrar la venta: {ex}",
                                   error=True)
            return None

    def get_sales(self):
        try:
            return self.service.get_sales()
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return []

    def get_today_stats(self):
        try:
            return self.service.get_today_stats()
        except Exception:
            return {"count": 0, "revenue": 0.0}
