# presentation/app.py

import flet as ft
from presentation.theme import AppTheme


class App:
    """
    Orquestador principal de la aplicación.
    Gestiona navegación, tema e inyección de dependencias.
    """

    def __init__(self, page: ft.Page):
        self.page = page
        self.is_dark = True
        self.current_route = "login"
        self._setup_page()
        self._init_dependencies()
        self.navigate_to("login")

    # ─── Page setup ───────────────────────────────────────────────
    def _setup_page(self):
        self.page.title = "NexaPOS"
        self.page.window_width = 1200
        self.page.window_height = 780
        self.page.window_min_width = 900
        self.page.window_min_height = 600
        self.page.window_center()
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme = ft.Theme(color_scheme_seed=AppTheme.ACCENT, use_material3=True)
        self.page.dark_theme = ft.Theme(color_scheme_seed=AppTheme.ACCENT, use_material3=True)
        self.page.bgcolor = AppTheme.DARK["bg"]
        self.page.padding = 0
        self.page.spacing = 0

    # ─── Dependency injection ─────────────────────────────────────
    def _init_dependencies(self):
        from infrastructure.repositories.auth_repository import AuthRepository
        from infrastructure.repositories.tenant_repository import TenantRepository
        from infrastructure.repositories.product_repository import ProductRepository
        from infrastructure.repositories.category_repository import CategoryRepository
        from infrastructure.repositories.sale_repository import SaleRepository
        from infrastructure.repositories.inventory_repository import InventoryRepository
        from domain.services.auth_service import AuthService
        from domain.services.product_service import ProductService
        from domain.services.category_service import CategoryService
        from domain.services.sale_service import SaleService
        from application.controllers.auth_controller import AuthController
        from application.controllers.product_controller import ProductController
        from application.controllers.category_controller import CategoryController
        from application.controllers.sale_controller import SaleController

        # Repos
        auth_repo = AuthRepository()
        tenant_repo = TenantRepository()
        product_repo = ProductRepository()
        category_repo = CategoryRepository()
        sale_repo = SaleRepository()
        inventory_repo = InventoryRepository()

        # Services
        auth_svc = AuthService(auth_repo, tenant_repo)
        product_svc = ProductService(product_repo)
        category_svc = CategoryService(category_repo)
        sale_svc = SaleService(sale_repo, inventory_repo)

        # Controllers
        self.auth_controller = AuthController(auth_svc, self)
        self.product_controller = ProductController(product_svc, self)
        self.category_controller = CategoryController(category_svc, self)
        self.sale_controller = SaleController(sale_svc, self)

    # ─── Navigation ───────────────────────────────────────────────
    def navigate_to(self, route: str):
        self.current_route = route
        self._render(route)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.page.theme_mode = ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
        self.page.bgcolor = self.get_colors()["bg"]
        self.page.update()
        self._render(self.current_route)

    def get_colors(self) -> dict:
        return AppTheme.DARK if self.is_dark else AppTheme.LIGHT

    # ─── Render ───────────────────────────────────────────────────
    def _render(self, route: str):
        from presentation.views.login_view import LoginView
        from presentation.views.register_view import RegisterView
        from presentation.views.dashboard_view import DashboardView
        from presentation.views.pos_view import PosView
        from presentation.views.products_view import ProductsView
        from presentation.views.categories_view import CategoriesView
        from presentation.views.sales_view import SalesView
        from presentation.components.main_layout import MainLayout

        colors = self.get_colors()

        # Auth routes (no sidebar)
        if route == "login":
            view = LoginView(self.page, colors, self.is_dark, self.auth_controller, self)
            self._set_content(view.build())
            return

        if route == "register":
            view = RegisterView(self.page, colors, self.is_dark, self.auth_controller, self)
            self._set_content(view.build())
            return

        # Protected routes (with sidebar)
        content_view = self._build_content_view(route, colors)
        layout = MainLayout(self.page, colors, self.is_dark, route, content_view, self)
        self._set_content(layout.build())

    def _build_content_view(self, route: str, colors: dict):
        from presentation.views.dashboard_view import DashboardView
        from presentation.views.pos_view import PosView
        from presentation.views.products_view import ProductsView
        from presentation.views.categories_view import CategoriesView
        from presentation.views.sales_view import SalesView

        views = {
            "dashboard": lambda: DashboardView(
                self.page, colors, self.is_dark,
                self.sale_controller, self.product_controller, self
            ),
            "pos": lambda: PosView(
                self.page, colors, self.is_dark,
                self.sale_controller, self.product_controller, self
            ),
            "products": lambda: ProductsView(
                self.page, colors, self.is_dark,
                self.product_controller, self.category_controller, self
            ),
            "categories": lambda: CategoriesView(
                self.page, colors, self.is_dark,
                self.category_controller, self
            ),
            "sales": lambda: SalesView(
                self.page, colors, self.is_dark,
                self.sale_controller, self
            ),
        }
        factory = views.get(route, views["dashboard"])
        return factory()

    def _set_content(self, control):
        if self.page is not None:
            self.page.controls.clear()  # type: ignore
            self.page.controls.append(  # type: ignore
                ft.Container(content=control, expand=True)
            )
            self.page.update()  # type: ignore

    # ─── Notifications ────────────────────────────────────────────
    def show_snackbar(self, message: str, error: bool = False):
        icon = ft.icons.ERROR_ROUNDED if error else ft.icons.CHECK_CIRCLE_ROUNDED
        color = AppTheme.ERROR if error else AppTheme.SUCCESS

        self.page.snack_bar = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(icon, color="white", size=18),
                    ft.Text(message, color="white", size=13, expand=True),
                ],
                spacing=10,
            ),
            bgcolor=color,
            duration=3000,
            behavior=ft.SnackBarBehavior.FLOATING,
        )
        self.page.snack_bar.open = True
        self.page.update()