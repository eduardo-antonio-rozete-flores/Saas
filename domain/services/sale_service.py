# domain/services/sale_service.py
#
# CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
#
# 1. __init__ ahora acepta `event_service` como parámetro opcional.
#    → Patrón: inyección de dependencia. El servicio no sabe si el
#      event_service existe; si no se inyecta (tests unitarios, CLI
#      simple), funciona igual que antes. Principio Open/Closed.
#
# 2. Después de completar una venta exitosa, emite el evento
#    "sale_created" con el payload mínimo necesario para analytics.
#    → El emit es "fire and forget": si falla el evento, la venta
#      YA fue registrada. Nunca revertimos una venta por un fallo
#      de observabilidad.
#
# 3. Se importa EventService solo para acceder a sus constantes de
#    tipo (strings de eventos). No hay acoplamiento de instancia.

from session.session import Session


class SaleService:

    def __init__(self, sale_repo, inventory_repo, event_service=None):
        """
        Args:
            sale_repo:      SaleRepository     (requerido)
            inventory_repo: InventoryRepository (requerido)
            event_service:  EventService        (opcional) — si se provee,
                            emite eventos de dominio tras cada venta.
        """
        self.sale_repo      = sale_repo
        self.inventory_repo = inventory_repo
        self.event_service  = event_service  # NUEVO

    def _require_auth(self):
        if not Session.tenant_id:
            raise Exception("No autenticado")

    # ------------------------------------------------------------------ #
    # Crear venta                                                         #
    # ------------------------------------------------------------------ #
    def create_sale(self, cart: list, payment_method: str, amount_received: float = 0):
        """
        cart: [{"id": uuid, "name": str, "price": float, "quantity": int}]
        payment_method: "cash" | "card" | "transfer"
        """
        self._require_auth()

        if not cart:
            raise ValueError("El carrito está vacío")

        valid_methods = ("cash", "card", "transfer")
        if payment_method not in valid_methods:
            raise ValueError("Método de pago inválido")

        total = sum(float(item["price"]) * int(item["quantity"]) for item in cart)

        if payment_method == "cash" and amount_received < total:
            raise ValueError(
                f"Monto insuficiente. Total: ${total:.2f}, recibido: ${amount_received:.2f}"
            )

        if Session.current_user is None:
            raise Exception("Usuario no autenticado")

        # 1. Registro de la venta
        sale_res = self.sale_repo.create_sale(
            {
                "tenant_id": Session.tenant_id,
                "user_id":   Session.current_user.id,
                "total":     total,
                "status":    "completed",
            }
        )
        if not sale_res.data:
            raise Exception("Error al registrar la venta")
        sale    = sale_res.data[0]
        sale_id = sale["id"]

        # 2. Items de venta
        items_data = [
            {
                "sale_id":    sale_id,
                "product_id": item["id"],
                "quantity":   int(item["quantity"]),
                "price":      float(item["price"]),
            }
            for item in cart
        ]
        try:
            self.sale_repo.create_sale_items(items_data)
        except Exception as e:
            raise Exception(f"Error al registrar items de venta: {e}")

        # 3. Registro de pago
        try:
            self.sale_repo.create_payment(
                {
                    "sale_id": sale_id,
                    "method":  payment_method,
                    "amount":  amount_received if payment_method == "cash" else total,
                }
            )
        except Exception as e:
            raise Exception(f"Error al registrar pago: {e}")

        # 4. Actualizar inventario (no crítico)
        for item in cart:
            try:
                self.inventory_repo.decrement_stock(item["id"], int(item["quantity"]))
                self.inventory_repo.log_movement(
                    item["id"], "sale", -int(item["quantity"]), sale_id
                )
            except Exception:
                pass

        # 5. NUEVO — Emitir evento de dominio (fire & forget)
        if self.event_service:
            try:
                self.event_service.emit(
                    Session.tenant_id,
                    "sale_created",
                    {
                        "sale_id":        sale_id,
                        "total":          total,
                        "items_count":    len(cart),
                        "payment_method": payment_method,
                        "items": [
                            {
                                "product_id": i["id"],
                                "name":       i.get("name", ""),
                                "quantity":   int(i["quantity"]),
                                "price":      float(i["price"]),
                            }
                            for i in cart
                        ],
                    },
                )
            except Exception:
                pass  # Nunca interrumpimos la venta por un fallo de eventos

        change = amount_received - total if payment_method == "cash" else 0
        return {
            "sale":  sale,
            "total": total,
            "change": change,
            # NUEVO: devolvemos los items para que pos_view pueda
            # construir el ticket sin tener que re-consultar la BD.
            "items": cart,
        }

    # ------------------------------------------------------------------ #
    # Consultas                                                           #
    # ------------------------------------------------------------------ #
    def get_sales(self):
        self._require_auth()
        res = self.sale_repo.get_all(Session.tenant_id)
        return res.data or []

    def get_today_stats(self):
        self._require_auth()
        res    = self.sale_repo.get_today_stats(Session.tenant_id)
        sales  = res.data or []
        count  = len(sales)
        revenue = sum(float(s.get("total", 0)) for s in sales)
        return {"count": count, "revenue": revenue}