# domain/services/product_service.py
#
# CAMBIOS (refactor arquitectural):
#   • _require_auth() lanza AuthenticationError (antes: Exception genérica).
#   • create_product() y update_product() usan CreateProductRequest /
#     UpdateProductRequest para validar y normalizar — la lógica de strip,
#     None-si-vacío, etc. ya no vive en el servicio sino en los DTOs.
#   • Lanza RepositoryError en vez de Exception para errores de DB.
#   • La firma pública no cambia: las vistas y controladores siguen
#     llamando create_product(data: dict).
#
# FASES ANTERIORES (Fase 4 — Código de Barras) conservadas:
#   • find_by_barcode() / generate_barcode_for()

from session.session import Session
from domain.schemas.product_schemas import CreateProductRequest, UpdateProductRequest
from domain.exceptions import AuthenticationError, RepositoryError, ValidationError


class ProductService:

    def __init__(self, repo):
        self.repo = repo

    def _require_auth(self) -> str:
        if not Session.tenant_id:
            raise AuthenticationError("No hay sesión activa")
        return Session.tenant_id

    # ─── Listado y búsqueda ───────────────────────────────────────

    def list_products(self):
        tenant_id = self._require_auth()
        res = self.repo.get_all(tenant_id)
        return res.data or []

    def search_products(self, query):
        tenant_id = self._require_auth()
        res = self.repo.search(tenant_id, query)
        return res.data or []

    # ─── Fase 4: Código de barras ─────────────────────────────────

    def find_by_barcode(self, barcode: str) -> dict | None:
        """
        Devuelve None (no lanza excepción) si el barcode no se encuentra,
        porque en el POS un barcode desconocido es un caso esperado.
        """
        tenant_id = self._require_auth()
        if not barcode or not barcode.strip():
            return None
        res  = self.repo.get_by_barcode(tenant_id, barcode.strip())
        data = res.data or []
        return data[0] if data else None

    def generate_barcode_for(self, product_id: str) -> str:
        numeric = "".join(c for c in product_id.replace("-", "") if c.isdigit())
        while len(numeric) < 12:
            numeric += "0"
        return numeric[:12]

    # ─── CRUD ─────────────────────────────────────────────────────

    def create_product(self, data: dict) -> dict:
        tenant_id = self._require_auth()

        try:
            price = float(data.get("price", 0))
            cost  = float(data.get("cost", 0))
        except (ValueError, TypeError):
            raise ValidationError("price", "Precio o costo con formato inválido")

        request = CreateProductRequest(
            name=data.get("name", ""),
            price=price,
            cost=cost,
            barcode=data.get("barcode"),
            barcode_type=data.get("barcode_type"),
            category_id=data.get("category_id"),
            is_active=data.get("is_active", True),
        )
        request.validate()  # ValidationError si datos inválidos

        res = self.repo.create(request.to_db_dict(tenant_id))
        if not res.data:
            raise RepositoryError("Error al crear el producto en base de datos")
        return res.data[0]

    def update_product(self, product_id: str, data: dict) -> dict:
        self._require_auth()

        try:
            price = float(data["price"]) if "price" in data else None
            cost  = float(data["cost"])  if "cost"  in data else None
        except (ValueError, TypeError):
            raise ValidationError("price", "Precio o costo con formato inválido")

        request = UpdateProductRequest(
            name=data.get("name"),
            price=price,
            cost=cost,
            barcode=data.get("barcode"),
            barcode_type=data.get("barcode_type"),
            category_id=data.get("category_id"),
            is_active=data.get("is_active"),
        )
        request.validate()

        res = self.repo.update(product_id, request.to_db_dict())
        if not res.data:
            raise RepositoryError("Error al actualizar el producto")
        return res.data[0]

    def delete_product(self, product_id: str) -> None:
        self._require_auth()
        self.repo.soft_delete(product_id)

    def get_count(self) -> int:
        tenant_id = self._require_auth()
        res = self.repo.count(tenant_id)
        return res.count or 0
