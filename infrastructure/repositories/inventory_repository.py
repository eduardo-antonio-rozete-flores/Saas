# infrastructure/repositories/inventory_repository.py
#
# CAMBIOS (Fase 5 — Inventario Inteligente):
#
# 1. get_kardex(product_id, tenant_id, limit) — consulta historial completo
#    vía la función RPC 'kardex_by_product' creada en la migración SQL.
#
# 2. add_kardex_entry(entry) — registra un movimiento en la tabla kardex
#    con saldo_anterior y saldo_posterior calculados por el servicio.
#    DECISIÓN: el cálculo del saldo lo hace InventoryService (dominio),
#    el repositorio solo persiste.
#
# 3. get_low_stock(tenant_id) — consulta vía RPC 'low_stock_products'.
#    Devuelve productos cuyo stock_actual <= stock_minimo.
#
# 4. decrement_stock ahora devuelve el stock_posterior para que
#    InventoryService pueda registrar el kardex correctamente.
#
# PRINCIPIO MANTENIDO: cero lógica de negocio en este archivo.

from config.supabase_client import supabase


class InventoryRepository:

    # ------------------------------------------------------------------ #
    # Consultas base                                                      #
    # ------------------------------------------------------------------ #
    def get_stock(self, product_id: str):
        return (
            supabase.table("inventory")
            .select("*")
            .eq("product_id", product_id)
            .execute()
        )

    def get_all(self, tenant_id: str):
        """
        Devuelve todo el inventario del tenant con datos del producto.
        DECISIÓN: usamos inner join via select anidado para obtener nombre,
        SKU y precio del producto en una sola query (evita N+1).
        """
        return (
            supabase.table("inventory")
            .select("*, products!inner(id, name, sku, price, cost, tenant_id, barcode)")
            .eq("products.tenant_id", tenant_id)
            .execute()
        )

    # ------------------------------------------------------------------ #
    # NUEVO Fase 5 — Productos con stock bajo                            #
    # ------------------------------------------------------------------ #
    def get_low_stock(self, tenant_id: str):
        """
        Llama a la función RPC low_stock_products.
        Devuelve productos donde stock_actual <= stock_minimo.
        """
        return supabase.rpc("low_stock_products", {"tenant": tenant_id}).execute()

    # ------------------------------------------------------------------ #
    # Upsert de stock                                                     #
    # ------------------------------------------------------------------ #
    def upsert(self, product_id: str, stock_actual: int, stock_minimo: int = 5):
        try:
            return (
                supabase.table("inventory")
                .upsert(
                    {
                        "product_id":   product_id,
                        "stock_actual": stock_actual,
                        "stock_minimo": stock_minimo,
                    },
                    on_conflict="product_id",
                )
                .execute()
            )
        except Exception as e:
            error_msg = str(e)
            if "row level security" in error_msg.lower():
                raise Exception("No tienes permisos para actualizar el inventario")
            raise

    def decrement_stock(self, product_id: str, quantity: int):
        """
        CAMBIO Fase 5: ahora devuelve (stock_anterior, stock_posterior)
        para que InventoryService pueda registrar el kardex.
        """
        current = self.get_stock(product_id)
        if current.data and len(current.data) > 0:
            stock_ant  = current.data[0]["stock_actual"] #type: ignore
            stock_min  = current.data[0]["stock_minimo"]#type:ignore
            stock_post = max(0, stock_ant - quantity) #type: ignore
            self.upsert(product_id, stock_post, stock_min) #type: ignore
            return stock_ant, stock_post
        return 0, 0

    # ------------------------------------------------------------------ #
    # Log de movimientos (tabla original — no se toca)                   #
    # ------------------------------------------------------------------ #
    def log_movement(self, product_id: str, movement_type: str,
                     quantity: int, reference_id=None):
        try:
            return (
                supabase.table("stock_movements")
                .insert(
                    {
                        "product_id":   product_id,
                        "type":         movement_type,
                        "quantity":     quantity,
                        "reference_id": reference_id,
                    }
                )
                .execute()
            )
        except Exception as e:
            error_msg = str(e)
            if "row level security" in error_msg.lower():
                raise Exception("No tienes permisos para registrar movimientos")
            raise

    # ------------------------------------------------------------------ #
    # NUEVO Fase 5 — Kardex                                              #
    # ------------------------------------------------------------------ #
    def add_kardex_entry(self, entry: dict):
        """
        Inserta una fila en la tabla 'kardex'.
        entry debe contener:
            tenant_id, product_id, tipo, cantidad,
            saldo_anterior, saldo_posterior,
            costo_unitario (opcional), referencia_id (opcional),
            referencia_tipo (opcional), notas (opcional)

        DECISIÓN: no calculamos saldos aquí — el servicio ya los trae
        calculados. El repositorio es un simple INSERT.
        """
        try:
            return supabase.table("kardex").insert(entry).execute()
        except Exception as e:
            # Kardex es observabilidad: no rompemos la operación principal
            print(f"[KARDEX WARNING] No se pudo registrar movimiento: {e}")
            return None

    def get_kardex(self, tenant_id: str, product_id: str, limit: int = 50):
        """
        Historial de movimientos de un producto vía RPC.
        Usa la función kardex_by_product creada en la migración.
        """
        return supabase.rpc(
            "kardex_by_product",
            {"p_tenant": tenant_id, "p_product": product_id, "p_limit": limit},
        ).execute()