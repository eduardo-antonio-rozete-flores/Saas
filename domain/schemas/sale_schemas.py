# domain/schemas/sale_schemas.py
#
# DTOs para operaciones de ventas.
#
# DECISIÓN: las reglas de negocio de validación (carrito vacío, monto
# insuficiente, método de pago inválido) viven en validate(), no en la vista
# ni en el servicio. La vista solo llama validate() y muestra el error.
#
# CreateSaleRequest.from_cart() actúa como adaptador entre el formato del
# carrito del POS (lista de dicts) y el DTO tipado.

from dataclasses import dataclass, field
from typing import List
from domain.exceptions import (
    ValidationError,
    EmptyCartError,
    InsufficientPaymentError,
)

# 'electronic' agregado para Fase 6 (recargas y pagos QR/CoDi)
VALID_PAYMENT_METHODS = ("cash", "card", "transfer", "electronic")


@dataclass
class SaleItemRequest:
    """Ítem individual dentro de una solicitud de venta."""
    product_id:   str
    product_name: str
    quantity:     int
    unit_price:   float

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity

    def validate(self) -> None:
        if self.quantity <= 0:
            raise ValidationError(
                "quantity",
                f"Cantidad inválida para '{self.product_name}': debe ser mayor a 0",
            )
        if self.unit_price <= 0:
            raise ValidationError(
                "unit_price",
                f"Precio inválido para '{self.product_name}': debe ser mayor a 0",
            )


@dataclass
class CreateSaleRequest:
    """DTO completo para registrar una venta."""
    items:           List[SaleItemRequest]
    payment_method:  str
    amount_received: float = 0.0

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def validate(self) -> None:
        if not self.items:
            raise EmptyCartError()
        if self.payment_method not in VALID_PAYMENT_METHODS:
            raise ValidationError(
                "payment_method",
                f"Método de pago inválido: '{self.payment_method}'",
            )
        for item in self.items:
            item.validate()
        if self.payment_method == "cash" and self.amount_received < self.total:
            raise InsufficientPaymentError(self.total, self.amount_received)

    @classmethod
    def from_cart(cls, cart: list, payment_method: str,
                  amount_received: float) -> "CreateSaleRequest":
        """
        Adaptador: convierte el carrito del POS (lista de dicts) al DTO.
        Formato del carrito: [{id, name, quantity, price}, ...]
        """
        items = [
            SaleItemRequest(
                product_id=item["id"],
                product_name=item.get("name", ""),
                quantity=int(item["quantity"]),
                unit_price=float(item["price"]),
            )
            for item in cart
        ]
        return cls(
            items=items,
            payment_method=payment_method,
            amount_received=amount_received,
        )
