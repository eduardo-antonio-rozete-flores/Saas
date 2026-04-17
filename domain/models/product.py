# domain/models/product.py
#
# Entidad de dominio: Producto.
#
# DIFERENCIA CON LOS DICTS DE SUPABASE:
#   Los dicts del repositorio son datos crudos.
#   Esta entidad es un objeto rico con comportamiento (margen, ganancia,
#   etc.) que encapsula las reglas del dominio sobre un producto.
#
# USO ACTUAL: como value objects tipados entre capas.
#   Los servicios pueden devolver Product en vez de dicts anónimos,
#   eliminando bugs por typos en claves de dict ("pice" vs "price").

from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Entidad de negocio para un producto del catálogo."""
    id:          str
    name:        str
    price:       float
    tenant_id:   str
    cost:        float         = 0.0
    barcode:     Optional[str] = None
    category_id: Optional[str] = None
    is_active:   bool          = True

    # ─── Comportamiento de dominio ────────────────────────────────

    @property
    def margin_pct(self) -> float:
        """Margen de ganancia como porcentaje sobre el precio de venta."""
        if self.price <= 0:
            return 0.0
        return (self.price - self.cost) / self.price * 100

    @property
    def profit(self) -> float:
        """Ganancia bruta por unidad vendida."""
        return self.price - self.cost

    def is_profitable(self) -> bool:
        """True si el precio de venta supera el costo."""
        return self.price > self.cost

    # ─── Conversión desde/hacia repositorio ──────────────────────

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """Construye la entidad desde un dict de Supabase."""
        return cls(
            id=data["id"],
            name=data["name"],
            price=float(data.get("price", 0)),
            tenant_id=data.get("tenant_id", ""),
            cost=float(data.get("cost", 0)),
            barcode=data.get("barcode"),
            category_id=data.get("category_id"),
            is_active=data.get("is_active", True),
        )

    def to_dict(self) -> dict:
        """Convierte la entidad de vuelta a dict (para repositorios o UI)."""
        return {
            "id":          self.id,
            "name":        self.name,
            "price":       self.price,
            "tenant_id":   self.tenant_id,
            "cost":        self.cost,
            "barcode":     self.barcode,
            "category_id": self.category_id,
            "is_active":   self.is_active,
        }
