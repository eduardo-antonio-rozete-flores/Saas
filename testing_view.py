import flet as ft
from infrastructure.repositories.auth_repository import AuthRepository
from infrastructure.repositories.product_repository import ProductRepository

from domain.services.auth_service import AuthService
from domain.services.product_service import ProductService

from application.controllers.auth_controller import AuthController
from application.controllers.product_controller import ProductController
from infrastructure.repositories.tenant_repository import TenantRepository

auth_repo = AuthRepository()
product_repo = ProductRepository()
tenant_repo = TenantRepository()
auth_service = AuthService(auth_repo, tenant_repo)
product_service = ProductService(product_repo)

auth_controller = AuthController(auth_service)
product_controller = ProductController(product_service)

def main(page: ft.Page):
    page.title = "Testing view"
    
    page.theme_mode = ft.ThemeMode.DARK

    email = ft.TextField(label="Email", width=300)
    password = ft.TextField(label="Password", width=300, password=True) 

    button = ft.ElevatedButton(text="Login", on_click= auth_controller.login())

    page.add(email, password, button)

ft.app(target = main)