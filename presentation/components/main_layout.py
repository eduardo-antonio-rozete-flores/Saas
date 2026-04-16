# presentation/components/main_layout.py
#
# CAMBIOS (Fase 5):
#   Se añadió "inventory" a NAV_ITEMS con ícono WAREHOUSE_ROUNDED.
#   Posición: entre Productos y Ventas — flujo lógico:
#   productos → inventario → ventas → analytics.
#
#   DECISIÓN: el item de Inventario usa color WARNING (naranja) cuando
#   hay alertas de stock bajo. El sidebar "respira" el estado del negocio.

import flet as ft
from presentation.theme import AppTheme
from session.session import Session


class MainLayout:

    NAV_ITEMS = [
        ("dashboard",  ft.icons.DASHBOARD_ROUNDED,      "Dashboard"),
        ("pos",        ft.icons.POINT_OF_SALE_ROUNDED,  "Punto de Venta"),
        ("products",   ft.icons.INVENTORY_2_ROUNDED,    "Productos"),
        ("inventory",  ft.icons.WAREHOUSE_ROUNDED,      "Inventario"),    # NUEVO Fase 5
        ("categories", ft.icons.CATEGORY_ROUNDED,       "Categorías"),
        ("sales",      ft.icons.RECEIPT_LONG_ROUNDED,   "Ventas"),
        ("analytics",  ft.icons.ANALYTICS_ROUNDED,      "Analytics"),
    ]

    def __init__(self, page, colors, is_dark, current_route,
                 content_view, app, has_low_stock: bool = False):
        self.page          = page
        self.colors        = colors
        self.is_dark       = is_dark
        self.current_route = current_route
        self.content_view  = content_view
        self.app           = app
        self.has_low_stock = has_low_stock  # NUEVO: para resaltar icono inventario

    def build(self):
        return ft.Row(
            [
                self._build_sidebar(),
                ft.Container(width=1, bgcolor=self.colors["border"]),
                ft.Container(
                    content=self.content_view.build(),
                    expand=True, bgcolor=self.colors["bg"], padding=0,
                ),
            ],
            expand=True, spacing=0,
        )

    def _build_sidebar(self):
        c = self.colors
        return ft.Container(
            content=ft.Column(
                [
                    self._logo_section(),
                    ft.Container(height=1, bgcolor=c["divider"]),
                    ft.Container(
                        content=ft.Column(
                            [self._nav_item(r, ic, lb) for r, ic, lb in self.NAV_ITEMS],
                            spacing=4,
                        ),
                        padding=ft.padding.symmetric(horizontal=12, vertical=16),
                        expand=True,
                    ),
                    ft.Container(height=1, bgcolor=c["divider"]),
                    self._bottom_section(),
                ],
                spacing=0, expand=True,
            ),
            width=224, bgcolor=c["sidebar"],
            border=ft.border.only(right=ft.border.BorderSide(1, c["border"])),
        )

    def _logo_section(self):
        c = self.colors
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text("N", color="white", size=18,
                                    weight=ft.FontWeight.BOLD),
                    width=38, height=38, border_radius=10,
                    gradient=AppTheme.gradient_primary(),
                    alignment=ft.alignment.center,
                ),
                ft.Column([
                    ft.Text("NexaPOS", size=15, weight=ft.FontWeight.BOLD,
                            color=c["text"]),
                    ft.Text("v2.0", size=11, color=c["text_secondary"]),
                ], spacing=0, tight=True),
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=16, vertical=20),
        )

    def _nav_item(self, route: str, icon, label: str):
        c         = self.colors
        is_active = self.current_route == route

        # NUEVO: Inventario con alerta usa color WARNING
        is_inventory_alert = (route == "inventory" and self.has_low_stock
                              and not is_active)

        if route == "analytics":
            accent_color    = AppTheme.SUCCESS
            active_gradient = AppTheme.gradient_success()
        elif route == "inventory" and is_inventory_alert:
            accent_color    = AppTheme.WARNING
            active_gradient = AppTheme.gradient_warning()
        else:
            accent_color    = AppTheme.ACCENT
            active_gradient = AppTheme.gradient_primary()

        icon_container = ft.Container(
            content=ft.Stack([
                ft.Icon(icon,
                        color="white" if is_active else
                              (AppTheme.WARNING if is_inventory_alert
                               else c["text_secondary"]),
                        size=18),
                # Punto de alerta rojo para inventario con stock bajo
                ft.Container(
                    width=8, height=8,
                    bgcolor=AppTheme.ERROR,
                    border_radius=4,
                    right=0, top=0,
                ) if is_inventory_alert else ft.Container(),
            ]),
            width=34, height=34, border_radius=9,
            gradient=active_gradient if is_active else None,
            bgcolor="transparent",
            alignment=ft.alignment.center,
        )

        return ft.Container(
            content=ft.Row([
                icon_container,
                ft.Text(
                    label, size=13,
                    color=c["text"] if is_active else
                          (AppTheme.WARNING if is_inventory_alert
                           else c["text_secondary"]),
                    weight=ft.FontWeight.W_600 if (is_active or is_inventory_alert)
                           else ft.FontWeight.NORMAL,
                ),
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=10, vertical=9),
            border_radius=11,
            bgcolor=f"{accent_color}18" if (is_active or is_inventory_alert)
                    else "transparent",
            on_click=lambda e, r=route: self.app.navigate_to(r),
            ink=True,
        )

    def _bottom_section(self):
        c       = self.colors
        email   = Session.get_email()
        initial = Session.get_email_initial()
        theme_icon  = ft.icons.DARK_MODE_ROUNDED if self.is_dark else ft.icons.LIGHT_MODE_ROUNDED
        theme_label = "Modo oscuro" if self.is_dark else "Modo claro"

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(theme_icon, color=c["text_secondary"], size=16),
                        ft.Text(theme_label, size=12, color=c["text_secondary"],
                                expand=True),
                        ft.Switch(
                            value=self.is_dark, active_color=AppTheme.ACCENT,
                            on_change=lambda e: self.app.toggle_theme(), scale=0.8,
                        ),
                    ], spacing=8),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.LOGOUT_ROUNDED, color=AppTheme.ERROR, size=16),
                        ft.Text("Cerrar sesión", color=AppTheme.ERROR, size=12),
                    ], spacing=8),
                    on_click=lambda e: self.app.auth_controller.logout(),
                    ink=True, border_radius=8,
                    padding=ft.padding.symmetric(vertical=6),
                ),
                ft.Container(height=1, bgcolor=c["divider"]),
                ft.Row([
                    ft.Container(
                        content=ft.Text(initial, color="white", size=13,
                                        weight=ft.FontWeight.BOLD),
                        width=32, height=32, border_radius=16,
                        gradient=AppTheme.gradient_primary(),
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([
                        ft.Text(email, size=11, color=c["text"], no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                max_lines=1, width=130),
                        ft.Text("Admin", size=10, color=c["text_secondary"]),
                    ], spacing=0, tight=True),
                ], spacing=10),
            ], spacing=10),
            padding=ft.padding.all(16),
        )