# domain/models/sale.py
#
# Entidades de dominio: Sale y SaleItem.

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class SaleItem:
    """Ítem individual dentro de una venta."""
    product_id:   str
    product_name: str
    quantity:     int
    unit_price:   float

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class Sale:
    """Entidad de dominio para una venta completa."""
    id:             str
    tenant_id:      str
    user_id:        str
    total:          float
    status:         str
    payment_method: str
    items:          List[SaleItem]     = field(default_factory=list)
    created_at:     Optional[datetime] = None
    change:         float              = 0.0

    @property
    def items_count(self) -> int:
        """Total de unidades vendidas (suma de todas las cantidades)."""
        return sum(item.quantity for item in self.items)

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @classmethod
    def from_dict(cls, data: dict, items: list = None) -> "Sale":  # type: ignore
        """Construye la entidad desde dicts de Supabase."""
        created_at = None
        raw = data.get("created_at")
        if raw and isinstance(raw, str):
            try:
                created_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                pass

        sale_items = [
            SaleItem(
                product_id=i.get("product_id", ""),
                product_name=i.get("name", ""),
                quantity=int(i.get("quantity", 0)),
                unit_price=float(i.get("price", 0)),
            )
            for i in (items or [])
        ]

        return cls(
            id=data["id"],
            tenant_id=data.get("tenant_id", ""),
            user_id=data.get("user_id", ""),
            total=float(data.get("total", 0)),
            status=data.get("status", "completed"),
            payment_method=data.get("payment_method", "cash"),
            items=sale_items,
            created_at=created_at,
        )
