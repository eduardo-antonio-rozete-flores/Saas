# infrastructure/repositories/product_repository.py
from config.supabase_client import supabase
class ProductRepository():

    def get_all(self, tenant_id):
        return supabase.table("products")\
            .select("*")\
            .eq("tenant_id", tenant_id)\
            .execute()

    def get_products_by_tenant(self, tenant_id):
        return supabase.table("products")

    def create(self, data):
        return supabase.table("products")\
            .insert(data)\
            .execute()