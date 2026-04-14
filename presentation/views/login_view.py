# presentation/views/login_view.py

import flet as ft
from presentation.theme import AppTheme


class LoginView:

    def __init__(self, page, colors, is_dark, auth_controller, app):
        self.page = page
        self.colors = colors
        self.is_dark = is_dark
        self.auth_controller = auth_controller
        self.app = app

        self.email_field = AppTheme.make_text_field(
            "Correo electrónico", "tu@email.com", colors=colors
        )
        self.password_field = AppTheme.make_text_field(
            "Contraseña", "••••••••", password=True, colors=colors
        )
        self.loading = False

    # ─────────────────────────────────────────────────────────────
    def build(self):
        c = self.colors

        def on_login(e):
            if self.loading:
                return
            self.loading = True
            login_btn.disabled = True
            self.page.update()
            self.auth_controller.login(
                self.email_field.value or "",
                self.password_field.value or "",
            )
            self.loading = False
            login_btn.disabled = False
            self.page.update()

        def on_enter(e):
            if e.key == "Enter":
                on_login(e)

        self.email_field.on_submit = on_login
        self.password_field.on_submit = on_login

        login_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.LOGIN_ROUNDED, color="white", size=18),
                    ft.Text(
                        "Iniciar Sesión",
                        color="white",
                        size=14,
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            gradient=AppTheme.gradient_primary(),
            border_radius=12,
            padding=ft.padding.symmetric(vertical=14),
            on_click=on_login,
            ink=True,
        )

        form = ft.Column(
            [
                ft.Text(
                    "Bienvenido",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=c["text"],
                ),
                ft.Text(
                    "Inicia sesión en tu cuenta",
                    size=14,
                    color=c["text_secondary"],
                ),
                ft.Container(height=28),
                self.email_field,
                ft.Container(height=12),
                self.password_field,
                ft.Container(height=24),
                login_btn,
                ft.Container(height=12),
                ft.Row(
                    [
                        ft.Text("¿No tienes cuenta?", size=13, color=c["text_secondary"]),
                        ft.TextButton(
                            "Regístrate",
                            style=ft.ButtonStyle(color=AppTheme.ACCENT),
                            on_click=lambda e: self.app.navigate_to("register"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                ),
            ],
            width=340,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        # Left decorative panel
        left_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.icons.POINT_OF_SALE_ROUNDED, color="white", size=72),
                    ft.Container(height=20),
                    ft.Text(
                        "NexaPOS",
                        color="white",
                        size=36,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.Text(
                        "Sistema de Punto de Venta\nModerno · Rápido · Multitenant",
                        color="white",
                        size=15,
                        text_align=ft.TextAlign.CENTER,
                        opacity=0.9,
                    ),
                    ft.Container(height=40),
                    self._feature_chip(ft.icons.SPEED_ROUNDED, "Velocidad de venta"),
                    ft.Container(height=10),
                    self._feature_chip(ft.icons.INVENTORY_ROUNDED, "Control de inventario"),
                    ft.Container(height=10),
                    self._feature_chip(ft.icons.ANALYTICS_ROUNDED, "Reportes en tiempo real"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            gradient=AppTheme.gradient_auth_panel(),
            expand=1,
            alignment=ft.alignment.center,
            padding=ft.padding.all(48),
        )

        # Right form panel
        right_panel = ft.Container(
            content=form,
            expand=1,
            alignment=ft.alignment.center,
            bgcolor=c["bg"],
        )

        return ft.Container(
            content=ft.Row([left_panel, right_panel], expand=True, spacing=0),
            expand=True,
            bgcolor=c["bg"],
        )

    @staticmethod
    def _feature_chip(icon, text):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, color="white", size=16),
                    ft.Text(text, color="white", size=13),
                ],
                spacing=8,
                tight=True,
            ),
            bgcolor="rgba(255,255,255,0.15)",
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        )