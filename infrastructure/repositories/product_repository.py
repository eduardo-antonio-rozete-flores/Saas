# infrastructure/repositories/product_repository.py

from config.supabase_client import supabase


class ProductRepository:

    def get_all(self, tenant_id):
        return (
            supabase.table("products")
            .select("*, categories(name)")
            .eq("tenant_id", tenant_id)
            .eq("is_active", True)
            .order("name")
            .execute()
        )

    def get_by_id(self, product_id):
        return (
            supabase.table("products")
            .select("*, categories(name)")
            .eq("id", product_id)
            .single()
            .execute()
        )

    def search(self, tenant_id, query):
        return (
            supabase.table("products")
            .select("*, categories(name)")
            .eq("tenant_id", tenant_id)
            .eq("is_active", True)
            .ilike("name", f"%{query}%")
            .execute()
        )

    def create(self, data):
        # Ensure tenant_id is present for RLS policy
        if "tenant_id" not in data or not data["tenant_id"]:
            raise ValueError("tenant_id es requerido para crear un producto")
        try:
            res = supabase.table("products").insert(data).execute()
            return res
        except Exception as e:
            error_msg = str(e)
            if "row level security" in error_msg.lower():
                raise Exception("No tienes permisos para crear productos en este espacio de trabajo")
            raise

    def update(self, product_id, data):
        try:
            return (
                supabase.table("products")
                .update(data)
                .eq("id", product_id)
                .execute()
            )
        except Exception as e:
            error_msg = str(e)
            if "row level security" in error_msg.lower():
                raise Exception("No tienes permisos para actualizar este producto")
            raise

    def soft_delete(self, product_id):
        try:
            return (
                supabase.table("products")
                .update({"is_active": False})
                .eq("id", product_id)
                .execute()
            )
        except Exception as e:
            error_msg = str(e)
            if "row level security" in error_msg.lower():
                raise Exception("No tienes permisos para eliminar este producto")
            raise

    def count(self, tenant_id):
        return (
            supabase.table("products")
            .select("id", count="exact") # type: ignore
            .eq("tenant_id", tenant_id)
            .eq("is_active", True)
            .execute()
        )