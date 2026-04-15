# presentation/app.py
#
# CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
#
# 1. _init_dependencies() ahora construye y conecta toda la cadena de
#    dependencias de Fases 1-3:
#      EventRepository → EventService
#      AnalyticsRepository → AnalyticsService → AnalyticsController
#      TicketRepository → TicketService (con event_service inyectado)
#
# 2. SaleService ahora recibe event_service → emite sale_created en cada venta.
#
# 3. Se exponen self.analytics_controller y self.ticket_service para que
#    las vistas (dashboard_view, analytics_view, pos_view) los consuman.
#
# 4. _build_content_view() agrega la ruta "analytics" → AnalyticsView.
#
# 5. _render() agrega la importación lazy de AnalyticsView.
#
# PRINCIPIO: este archivo es el único "Composition Root" de la app.
# Ningún servicio/controlador crea sus propias dependencias.

import flet as ft
from presentation.theme import AppTheme


class App:
    """
    Orquestador principal de la aplicación.
    Gestiona navegación, tema e inyección de dependencias.
    """

    def __init__(self, page: ft.Page):
        self.page          = page
        self.is_dark       = True
        self.current_route = "login"
        self._setup_page()
        self._init_dependencies()
        self.navigate_to("login")

    # ─── Page setup ───────────────────────────────────────────────
    def _setup_page(self):
        self.page.title          = "NexaPOS"
        self.page.auto_scroll    = True
        self.page.window_width   = 1200
        self.page.window_height  = 780
        self.page.window_min_width  = 900
        self.page.window_min_height = 600
        self.page.window_center()
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.theme      = ft.Theme(color_scheme_seed=AppTheme.ACCENT, use_material3=True)
        self.page.dark_theme = ft.Theme(color_scheme_seed=AppTheme.ACCENT, use_material3=True)
        self.page.bgcolor    = AppTheme.DARK["bg"]
        self.page.padding    = 0
        self.page.spacing    = 0

    # ─── Dependency injection (Composition Root) ─────────────────
    def _init_dependencies(self):
        # ── Repositorios ──────────────────────────────────────────
        from infrastructure.repositories.auth_repository       import AuthRepository
        from infrastructure.repositories.tenant_repository     import TenantRepository
        from infrastructure.repositories.product_repository    import ProductRepository
        from infrastructure.repositories.category_repository   import CategoryRepository
        from infrastructure.repositories.sale_repository       import SaleRepository
        from infrastructure.repositories.inventory_repository  import InventoryRepository
        from infrastructure.repositories.event_repository      import EventRepository      # Fase 1
        from infrastructure.repositories.analytics_repository  import AnalyticsRepository  # Fase 2
        from infrastructure.repositories.ticket_repository     import TicketRepository     # Fase 3

        auth_repo       = AuthRepository()
        tenant_repo     = TenantRepository()
        product_repo    = ProductRepository()
        category_repo   = CategoryRepository()
        sale_repo       = SaleRepository()
        inventory_repo  = InventoryRepository()
        event_repo      = EventRepository()        # Fase 1
        analytics_repo  = AnalyticsRepository()    # Fase 2
        ticket_repo     = TicketRepository()       # Fase 3

        # ── Servicios ─────────────────────────────────────────────
        from domain.services.auth_service       import AuthService
        from domain.services.product_service    import ProductService
        from domain.services.category_service   import CategoryService
        from domain.services.sale_service       import SaleService
        from domain.services.event_service      import EventService      # Fase 1
        from domain.services.analytics_service  import AnalyticsService  # Fase 2
        from domain.services.ticket_service     import TicketService     # Fase 3

        auth_svc      = AuthService(auth_repo, tenant_repo)
        product_svc   = ProductService(product_repo)
        category_svc  = CategoryService(category_repo)
        event_svc     = EventService(event_repo)                         # Fase 1 — se inyecta abajo
        analytics_svc = AnalyticsService(analytics_repo)                 # Fase 2

        # CAMBIO: SaleService ahora recibe event_service para emitir sale_created
        sale_svc = SaleService(
            sale_repo      = sale_repo,
            inventory_repo = inventory_repo,
            event_service  = event_svc,        # Fase 1 integración
        )

        # Fase 3: TicketService con historial y eventos
        ticket_svc = TicketService(
            ticket_repo   = ticket_repo,
            event_service = event_svc,
        )

        # ── Controladores ─────────────────────────────────────────
        from application.controllers.auth_controller       import AuthController
        from application.controllers.product_controller    import ProductController
        from application.controllers.category_controller   import CategoryController
        from application.controllers.sale_controller       import SaleController
        from application.controllers.analytics_controller  import AnalyticsController  # Fase 2

        self.auth_controller      = AuthController(auth_svc, self)
        self.product_controller   = ProductController(product_svc, self)
        self.category_controller  = CategoryController(category_svc, self)
        self.sale_controller      = SaleController(sale_svc, self)
        self.analytics_controller = AnalyticsController(analytics_svc)   # Fase 2
        self.ticket_service       = ticket_svc                            # Fase 3 — accesible desde pos_view

    # ─── Navigation ───────────────────────────────────────────────
    def navigate_to(self, route: str):
        self.current_route = route
        self._render(route)

    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.page.theme_mode = ft.ThemeMode.DARK if self.is_dark else ft.ThemeMode.LIGHT
        self.page.bgcolor    = self.get_colors()["bg"]
        self.page.update()
        self._render(self.current_route)

    def get_colors(self) -> dict:
        return AppTheme.DARK if self.is_dark else AppTheme.LIGHT

    # ─── Render ───────────────────────────────────────────────────
    def _render(self, route: str):
        from presentation.views.login_view    import LoginView
        from presentation.views.register_view import RegisterView
        from presentation.components.main_layout import MainLayout

        colors = self.get_colors()

        if route == "login":
            view = LoginView(self.page, colors, self.is_dark, self.auth_controller, self)
            self._set_content(view.build())
            return

        if route == "register":
            view = RegisterView(self.page, colors, self.is_dark, self.auth_controller, self)
            self._set_content(view.build())
            return

        content_view = self._build_content_view(route, colors)
        layout       = MainLayout(self.page, colors, self.is_dark, route, content_view, self)
        self._set_content(layout.build())

    def _build_content_view(self, route: str, colors: dict):
        from presentation.views.dashboard_view  import DashboardView
        from presentation.views.pos_view        import PosView
        from presentation.views.products_view   import ProductsView
        from presentation.views.categories_view import CategoriesView
        from presentation.views.sales_view      import SalesView
        from presentation.views.analytics_view  import AnalyticsView   # NUEVO Fase 2

        views = {
            "dashboard": lambda: DashboardView(
                self.page, colors, self.is_dark,
                self.sale_controller, self.product_controller,
                self.analytics_controller, self,               # CAMBIO: analytics_controller añadido
            ),
            "pos": lambda: PosView(
                self.page, colors, self.is_dark,
                self.sale_controller, self.product_controller,
                self.ticket_service, self,                     # CAMBIO: ticket_service añadido
            ),
            "products": lambda: ProductsView(
                self.page, colors, self.is_dark,
                self.product_controller, self.category_controller, self,
            ),
            "categories": lambda: CategoriesView(
                self.page, colors, self.is_dark,
                self.category_controller, self,
            ),
            "sales": lambda: SalesView(
                self.page, colors, self.is_dark,
                self.sale_controller, self,
            ),
            # NUEVO Fase 2
            "analytics": lambda: AnalyticsView(
                self.page, colors, self.is_dark,
                self.analytics_controller, self,
            ),
        }
        factory = views.get(route, views["dashboard"])
        return factory()

    def _set_content(self, control):
        if self.page is not None:
            self.page.controls.clear()    # type: ignore
            self.page.controls.append(    # type: ignore
                ft.Container(content=control, expand=True)
            )
            self.page.update()            # type: ignore

    # ─── Notifications ────────────────────────────────────────────
    def show_snackbar(self, message: str, error: bool = False):
        icon  = ft.icons.ERROR_ROUNDED if error else ft.icons.CHECK_CIRCLE_ROUNDED
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