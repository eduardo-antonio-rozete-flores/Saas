# domain/services/product_service.py
#
# CAMBIOS (Fase 4 — Código de Barras):
#
# 1. find_by_barcode(barcode) — nueva operación de dominio.
#    DECISIÓN: la lógica de "si el barcode está vacío no busques" vive aquí,
#    no en el repositorio ni en la vista. Principio Single Responsibility.
#
# 2. create_product / update_product — ahora aceptan y normalizan
#    el campo 'barcode' (strip de espacios, None si vacío).
#
# 3. generate_barcode(product_id) — helper para asignar un EAN-13 básico
#    basado en el UUID del producto. No requiere librería externa.
#    Si en el futuro se necesita un barcode real (con imagen),
#    se delega a un servicio de infraestructura separado.

from session.session import Session


class ProductService:

    def __init__(self, repo):
        self.repo = repo

    def _require_auth(self):
        if not Session.tenant_id:
            raise Exception("No autenticado")

    def list_products(self):
        self._require_auth()
        res = self.repo.get_all(Session.tenant_id)
        return res.data or []

    def search_products(self, query):
        self._require_auth()
        res = self.repo.search(Session.tenant_id, query)
        return res.data or []

    # ------------------------------------------------------------------ #
    # NUEVO Fase 4 — Búsqueda por código de barras                      #
    # ------------------------------------------------------------------ #
    def find_by_barcode(self, barcode: str) -> dict | None:
        """
        Busca un producto activo por su código de barras exacto.

        Args:
            barcode: Código de barras escaneado o tipeado.

        Returns:
            Dict del producto si se encuentra, None si no.

        DECISIÓN: devolvemos None (no lanzamos excepción) porque en el POS
        un barcode no encontrado es un caso esperado, no un error del sistema.
        La vista decide cómo informarlo al cajero.
        """
        self._require_auth()
        if not barcode or not barcode.strip():
            return None
        res = self.repo.get_by_barcode(Session.tenant_id, barcode.strip())
        data = res.data or []
        return data[0] if data else None

    # ------------------------------------------------------------------ #
    # NUEVO Fase 4 — Asignar barcode automático                         #
    # ------------------------------------------------------------------ #
    def generate_barcode_for(self, product_id: str) -> str:
        """
        Genera un código numérico de 12 dígitos derivado del UUID del producto.
        No es un EAN-13 estándar (falta dígito verificador), es un identificador
        interno útil para pruebas. En producción real se reemplaza por un
        generador de EAN-13 certificado.

        DECISIÓN: mantenemos esto en el servicio (dominio) porque la regla
        de qué constituye un barcode válido para este negocio es lógica de
        negocio, no infraestructura.
        """
        numeric = "".join(c for c in product_id.replace("-", "") if c.isdigit())
        # Rellenar hasta 12 dígitos si el UUID no tiene suficientes dígitos
        while len(numeric) < 12:
            numeric += "0"
        return numeric[:12]

    # ------------------------------------------------------------------ #
    # CRUD (con barcode)                                                 #
    # ------------------------------------------------------------------ #
    def create_product(self, data: dict):
        self._require_auth()
        if not data.get("name", "").strip():
            raise ValueError("El nombre es requerido")
        try:
            price = float(data.get("price", 0))
        except (ValueError, TypeError):
            raise ValueError("Precio inválido")
        if price <= 0:
            raise ValueError("El precio debe ser mayor a 0")

        data["name"]      = data["name"].strip()
        data["price"]     = price
        data["cost"]      = float(data.get("cost", 0))
        data["tenant_id"] = Session.tenant_id
        data.setdefault("is_active", True)

        # Normalizar barcode — NUEVO Fase 4
        barcode = data.get("barcode", "")
        data["barcode"] = barcode.strip() if barcode and barcode.strip() else None

        # Normalizar category_id
        category_id = data.get("category_id")
        if not category_id or category_id == "":
            data["category_id"] = None

        res = self.repo.create(data)
        if not res.data:
            raise Exception("Error al crear producto")
        return res.data[0]

    def update_product(self, product_id: str, data: dict):
        self._require_auth()
        if "name" in data and not data["name"].strip():
            raise ValueError("El nombre es requerido")
        if "price" in data:
            try:
                data["price"] = float(data["price"])
            except (ValueError, TypeError):
                raise ValueError("Precio inválido")

        # Normalizar barcode — NUEVO Fase 4
        if "barcode" in data:
            bc = data.get("barcode", "")
            data["barcode"] = bc.strip() if bc and bc.strip() else None

        # Normalizar category_id
        if "category_id" in data:
            category_id = data.get("category_id")
            if not category_id or category_id == "":
                data["category_id"] = None

        res = self.repo.update(product_id, data)
        if not res.data:
            raise Exception("Error al actualizar producto")
        return res.data[0]

    def delete_product(self, product_id: str):
        self._require_auth()
        self.repo.soft_delete(product_id)

    def get_count(self):
        self._require_auth()
        res = self.repo.count(Session.tenant_id)
        return res.count or 0