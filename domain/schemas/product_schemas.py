# domain/schemas/product_schemas.py
#
# DTOs para operaciones de productos.
#
# DECISIÓN: la normalización de datos (strip, None si vacío, etc.)
# vive en to_db_dict() del DTO, no en el repositorio ni en la vista.
# Así hay un único lugar donde se define el formato de persistencia.

import uuid
from dataclasses import dataclass
from typing import Optional
from domain.exceptions import ValidationError

# Tipos válidos según CHECK constraint en BD.
# 'qr' incluido para pagos CoDi / QR del mercado mexicano.
VALID_BARCODE_TYPES = ("ean13", "upc", "code128", "ean8", "qr", "custom")


@dataclass
class CreateProductRequest:
    """DTO para crear un producto nuevo."""
    name:         str
    price:        float
    cost:         float         = 0.0
    barcode:      Optional[str] = None
    barcode_type: Optional[str] = None
    category_id:  Optional[str] = None
    is_active:    bool          = True

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValidationError("name", "El nombre del producto es requerido")
        if self.price <= 0:
            raise ValidationError("price", "El precio debe ser mayor a 0")
        if self.cost < 0:
            raise ValidationError("cost", "El costo no puede ser negativo")
        if self.barcode_type is not None and self.barcode_type not in VALID_BARCODE_TYPES:
            raise ValidationError(
                "barcode_type",
                f"Tipo de código de barras inválido. Válidos: {', '.join(VALID_BARCODE_TYPES)}",
            )

    def to_db_dict(self, tenant_id: str) -> dict:
        """Genera el dict listo para insertar en el repositorio.
        Si no se provee barcode se genera un placeholder PENDING-XXXXXXXX
        porque la columna es NOT NULL en BD.
        """
        barcode = self.barcode.strip() if self.barcode and self.barcode.strip() else None
        if barcode is None:
            barcode = f"PENDING-{uuid.uuid4().hex[:8].upper()}"

        d: dict = {
            "name":        self.name.strip(),
            "price":       self.price,
            "cost":        self.cost,
            "barcode":     barcode,
            "category_id": self.category_id or None,
            "is_active":   self.is_active,
            "tenant_id":   tenant_id,
        }
        if self.barcode_type:
            d["barcode_type"] = self.barcode_type
        return d


@dataclass
class UpdateProductRequest:
    """DTO para actualizar un producto existente.
    Todos los campos son opcionales: solo se actualiza lo que se pase.
    """
    name:         Optional[str]   = None
    price:        Optional[float] = None
    cost:         Optional[float] = None
    barcode:      Optional[str]   = None
    barcode_type: Optional[str]   = None
    category_id:  Optional[str]   = None
    is_active:    Optional[bool]  = None

    def validate(self) -> None:
        if self.name is not None and not self.name.strip():
            raise ValidationError("name", "El nombre del producto es requerido")
        if self.price is not None and self.price <= 0:
            raise ValidationError("price", "El precio debe ser mayor a 0")
        if self.cost is not None and self.cost < 0:
            raise ValidationError("cost", "El costo no puede ser negativo")
        if self.barcode_type is not None and self.barcode_type not in VALID_BARCODE_TYPES:
            raise ValidationError(
                "barcode_type",
                f"Tipo de código de barras inválido. Válidos: {', '.join(VALID_BARCODE_TYPES)}",
            )

    def to_db_dict(self) -> dict:
        """Genera el dict con solo los campos que se van a actualizar."""
        d: dict = {}
        if self.name is not None:
            d["name"] = self.name.strip()
        if self.price is not None:
            d["price"] = self.price
        if self.cost is not None:
            d["cost"] = self.cost
        if self.barcode is not None:
            d["barcode"] = self.barcode.strip() if self.barcode.strip() else None
        if self.barcode_type is not None:
            d["barcode_type"] = self.barcode_type
        if self.category_id is not None:
            d["category_id"] = self.category_id or None
        if self.is_active is not None:
            d["is_active"] = self.is_active
        return d
