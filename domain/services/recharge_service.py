# domain/services/recharge_service.py
#
# NUEVA — Fase 6: Recargas Electrónicas
#
# JUSTIFICACIÓN:
# Las recargas son una fuente de ingresos adicional muy común en tiendas
# de conveniencia en México. Este servicio implementa el mock inicial
# (Fase 6, paso 1) para que la UI pueda integrarse de inmediato.
# La integración con la API real (e.g. Multi, Telecard, Transfermóvil)
# se añade en una fase posterior reemplazando solo _call_provider_api().
#
# ESTRUCTURA:
#   • OPERATORS: catálogo de operadoras y montos disponibles (no hardcoded en UI)
#   • recharge(): orquesta validación → mock API → registro de evento
#   • get_history(): historial de recargas del tenant
#
# PATRÓN:
#   Idéntico al resto de servicios: recibe repos/services por inyección.
#   La vista nunca sabe si la API es real o mock — solo ve el resultado.
#
# ESCALABILIDAD:
#   Para conectar una API real, solo se modifica _call_provider_api().
#   El resto del servicio, la vista y el controlador no cambian.

import uuid
from datetime import datetime
from session.session import Session


class RechargeService:

    # ------------------------------------------------------------------ #
    # Catálogo de operadoras y montos (reglas de negocio, viven aquí)   #
    # ------------------------------------------------------------------ #
    OPERATORS = {
        "telcel": {
            "name":    "Telcel",
            "amounts": [10, 20, 30, 50, 100, 150, 200, 300, 500],
            "commission_pct": 0.03,   # 3% de comisión al negocio
        },
        "att": {
            "name":    "AT&T",
            "amounts": [10, 20, 30, 50, 100, 200, 300],
            "commission_pct": 0.035,
        },
        "movistar": {
            "name":    "Movistar",
            "amounts": [20, 30, 50, 100, 150, 200],
            "commission_pct": 0.03,
        },
        "unefon": {
            "name":    "Unefon",
            "amounts": [10, 20, 30, 50, 100],
            "commission_pct": 0.04,
        },
        "virgin": {
            "name":    "Virgin Mobile",
            "amounts": [20, 50, 100, 200],
            "commission_pct": 0.035,
        },
    }

    def __init__(self, event_service=None, recharge_repo=None):
        """
        Args:
            event_service:  EventService (opcional) — emite recharge_completed
            recharge_repo:  RechargeRepository (opcional) — historial en BD.
                            Si no se inyecta, el historial es solo en memoria
                            (suficiente para el mock de Fase 6).
        """
        self.event_service = event_service
        self.recharge_repo = recharge_repo
        # Historial en memoria como fallback cuando no hay repo
        self._memory_history: list[dict] = []

    def _require_auth(self):
        if not Session.tenant_id:
            raise Exception("[RechargeService] No autenticado")
        return Session.tenant_id

    # ------------------------------------------------------------------ #
    # Catálogo                                                            #
    # ------------------------------------------------------------------ #
    def get_operators(self) -> list[dict]:
        """Devuelve lista de operadoras disponibles con sus montos."""
        return [
            {"id": op_id, "name": info["name"], "amounts": info["amounts"]}
            for op_id, info in self.OPERATORS.items()
        ]

    def get_amounts_for(self, operator_id: str) -> list[int]:
        op = self.OPERATORS.get(operator_id)
        if not op:
            raise ValueError(f"Operadora desconocida: {operator_id}")
        return op["amounts"]

    # ------------------------------------------------------------------ #
    # Ejecutar recarga                                                    #
    # ------------------------------------------------------------------ #
    def recharge(self, phone: str, operator_id: str, amount: int) -> dict:
        """
        Procesa una recarga electrónica.

        Args:
            phone:       Número a 10 dígitos.
            operator_id: Clave de OPERATORS (telcel, att, etc.)
            amount:      Monto en pesos (debe estar en OPERATORS[op].amounts)

        Returns:
            {
                "success":      bool,
                "folio":        str,    # Referencia de la transacción
                "phone":        str,
                "operator":     str,    # Nombre de la operadora
                "amount":       int,
                "commission":   float,  # Ganancia del negocio
                "timestamp":    str,    # ISO
                "message":      str,
            }

        DECISIÓN: nunca lanzamos excepción en el flow principal —
        devolvemos success=False con message descriptivo para que la UI
        lo muestre como alerta, no como crash.
        """
        tenant_id = self._require_auth()

        # Validaciones de dominio
        phone_clean = "".join(c for c in phone if c.isdigit())
        if len(phone_clean) != 10:
            return {
                "success": False, "message": "El número debe tener 10 dígitos",
                "phone": phone, "operator": operator_id, "amount": amount,
            }

        op = self.OPERATORS.get(operator_id)
        if not op:
            return {
                "success": False,
                "message": f"Operadora '{operator_id}' no disponible",
                "phone": phone, "operator": operator_id, "amount": amount,
            }

        if amount not in op["amounts"]:
            return {
                "success": False,
                "message": f"Monto ${amount} no disponible para {op['name']}",
                "phone": phone, "operator": op["name"], "amount": amount,
            }

        # Llamar al proveedor (mock por ahora)
        api_result = self._call_provider_api(phone_clean, operator_id, amount)

        commission = round(amount * op["commission_pct"], 2)
        folio      = api_result.get("folio", f"REC-{str(uuid.uuid4())[:8].upper()}")
        timestamp  = datetime.now().isoformat(timespec="seconds")

        result = {
            "success":    api_result.get("success", False),
            "folio":      folio,
            "phone":      phone_clean,
            "operator":   op["name"],
            "amount":     amount,
            "commission": commission,
            "timestamp":  timestamp,
            "message":    api_result.get("message", "Recarga procesada"),
            "tenant_id":  tenant_id,
        }

        if result["success"]:
            # Guardar en historial
            self._save_to_history(result)

            # Emitir evento (fire & forget)
            if self.event_service:
                try:
                    self.event_service.emit(
                        tenant_id, "recharge_completed",
                        {"folio": folio, "amount": amount,
                         "operator": op["name"], "commission": commission},
                    )
                except Exception:
                    pass

        return result

    # ------------------------------------------------------------------ #
    # Historial de recargas                                              #
    # ------------------------------------------------------------------ #
    def get_history(self, limit: int = 50) -> list[dict]:
        """
        Devuelve el historial de recargas del tenant.
        Usa el repo si está disponible, si no devuelve la memoria.
        """
        tenant_id = self._require_auth()
        if self.recharge_repo:
            try:
                res = self.recharge_repo.get_by_tenant(tenant_id, limit)
                return res.data or []
            except Exception:
                pass
        return list(reversed(self._memory_history[-limit:]))

    # ------------------------------------------------------------------ #
    # Privados                                                            #
    # ------------------------------------------------------------------ #
    def _call_provider_api(self, phone: str, operator_id: str, amount: int) -> dict:
        """
        MOCK — Fase 6, paso 1.
        En Fase 6 paso 3 esta función llama la API real del proveedor
        (Multi, Telecard, etc.) sin cambiar nada más en el servicio.

        DECISIÓN: retornamos éxito siempre en el mock con un folio generado.
        El número de teléfono 0000000000 fuerza un fallo (útil para pruebas).
        """
        if phone == "0000000000":
            return {"success": False, "message": "Número inválido (prueba de fallo)"}

        return {
            "success": True,
            "folio":   f"REC-{str(uuid.uuid4())[:8].upper()}",
            "message": f"Recarga de ${amount} aplicada exitosamente",
        }

    def _save_to_history(self, result: dict) -> None:
        """Guarda en repo o en memoria según disponibilidad."""
        if self.recharge_repo:
            try:
                self.recharge_repo.save(result)
                return
            except Exception:
                pass
        # Fallback a memoria
        self._memory_history.append(result)