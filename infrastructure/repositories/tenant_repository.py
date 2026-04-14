# infrastructure/repositories/tenant_repository.py

from config.supabase_client import supabase

class TenantRepository:

    def create(self, data):
        try:
            res = supabase.table("tenants").insert(data).execute()
            return res
        except Exception as e:
            error_msg = str(e)
            if "row level security" in error_msg.lower():
                raise Exception("No tienes permisos para crear espacios de trabajo")
            raise

    def get_by_id(self, tenant_id):
        return (
            supabase.table("tenants")
            .select("*")
            .eq("id", tenant_id)
            .single()
            .execute()
        )