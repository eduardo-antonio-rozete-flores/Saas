# application/controllers/recharge_controller.py
#
# NUEVA — Fase 6: Recargas Electrónicas
#
# RESPONSABILIDAD:
#   Puente entre RechargeView/PosView y RechargeService.
#   Exposición del catálogo de operadoras para que la UI se construya
#   dinámicamente (no hardcoded en la vista).

class RechargeController:

    def __init__(self, service, app):
        self.service = service
        self.app     = app

    def get_operators(self) -> list:
        """Devuelve el catálogo de operadoras para poblar el Dropdown en la UI."""
        try:
            return self.service.get_operators()
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return []

    def get_amounts_for(self, operator_id: str) -> list:
        try:
            return self.service.get_amounts_for(operator_id)
        except Exception:
            return []

    def process_recharge(self, phone: str, operator_id: str, amount: int) -> dict | None:
        """
        Procesa una recarga y muestra snackbar apropiado.

        Returns:
            dict con resultado si éxito, None si falló.
        """
        try:
            result = self.service.recharge(phone, operator_id, amount)
            if result.get("success"):
                commission = result.get("commission", 0)
                self.app.show_snackbar(
                    f"✓ Recarga exitosa | Folio: {result['folio']} | Comisión: ${commission:.2f}"
                )
                return result
            else:
                self.app.show_snackbar(result.get("message", "Error en recarga"), error=True)
                return None
        except Exception as ex:
            self.app.show_snackbar(str(ex), error=True)
            return None

    def get_history(self) -> list:
        try:
            return self.service.get_history()
        except Exception:
            return []