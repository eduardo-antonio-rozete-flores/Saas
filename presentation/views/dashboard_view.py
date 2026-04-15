# presentation/views/dashboard_view.py
#
# CAMBIOS RESPECTO A LA VERSIÓN ANTERIOR:
#
# 1. __init__ ahora recibe `analytics_controller` como parámetro.
#    → Permite mostrar métricas reales (total_revenue, avg_ticket, growth_rate)
#      sin depender de datos mock.
#
# 2. Se añade una cuarta stat card "Ticket Promedio" usando analytics.
#    (Antes era "Total ventas" que era redundante con "Ventas hoy".)
#
# 3. Se añade un Quick Action "Ver Analytics" que navega a la vista completa.
#
# 4. Se mantiene todo el diseño y paleta existente (cero regresiones visuales).

import flet as ft
from presentation.theme import AppTheme
from session.session import Session


class DashboardView:

    def __init__(self, page, colors, is_dark, sale_controller,
                 product_controller, analytics_controller, app):  # CAMBIO: analytics_controller
        self.page                = page
        self.colors              = colors
        self.is_dark             = is_dark
        self.sale_controller     = sale_controller
        self.product_controller  = product_controller
        self.analytics_ctrl      = analytics_controller  # NUEVO
        self.app                 = app

    def build(self):
        c = self.colors

        # Datos existentes
        stats         = self.sale_controller.get_today_stats()
        product_count = self.product_controller.get_count()
        sales         = self.sale_controller.get_sales()
        recent        = sales[:5]
        today_sales   = stats.get("count", 0)
        today_revenue = stats.get("revenue", 0.0)

        # NUEVO: datos de analytics (avg ticket)
        analytics_data = {}
        try:
            analytics_data = self.analytics_ctrl.get_dashboard()
        except Exception:
            pass  # Si analytics falla, el dashboard sigue funcionando

        avg_ticket = analytics_data.get("avg_ticket", 0.0)

        stat_row = ft.Row(
            [
                AppTheme.stat_card(
                    "Ventas hoy",
                    today_sales,
                    ft.icons.RECEIPT_ROUNDED,
                    AppTheme.gradient_primary(),
                    c,
                ),
                AppTheme.stat_card(
                    "Ingresos hoy",
                    f"${today_revenue:,.2f}",
                    ft.icons.ATTACH_MONEY_ROUNDED,
                    AppTheme.gradient_success(),
                    c,
                ),
                AppTheme.stat_card(
                    "Productos activos",
                    product_count,
                    ft.icons.INVENTORY_2_ROUNDED,
                    AppTheme.gradient_warning(),
                    c,
                ),
                # CAMBIO: reemplazamos "Total ventas" por "Ticket Promedio" (más útil)
                AppTheme.stat_card(
                    "Ticket Promedio",
                    f"${avg_ticket:,.2f}",
                    ft.icons.ANALYTICS_ROUNDED,
                    AppTheme.gradient_info(),
                    c,
                ),
            ],
            spacing=16,
        )

        recent_table  = self._build_recent_sales(recent)

        quick_actions = ft.Row(
            [
                self._quick_action(
                    "Nueva Venta",
                    ft.icons.ADD_SHOPPING_CART_ROUNDED,
                    AppTheme.gradient_primary(),
                    lambda e: self.app.navigate_to("pos"),
                ),
                self._quick_action(
                    "Agregar Producto",
                    ft.icons.ADD_BOX_ROUNDED,
                    AppTheme.gradient_success(),
                    lambda e: self.app.navigate_to("products"),
                ),
                self._quick_action(
                    "Ver Ventas",
                    ft.icons.RECEIPT_LONG_ROUNDED,
                    AppTheme.gradient_info(),
                    lambda e: self.app.navigate_to("sales"),
                ),
                # NUEVO: acceso directo a Analytics
                self._quick_action(
                    "Analytics",
                    ft.icons.ANALYTICS_ROUNDED,
                    AppTheme.gradient_warning(),
                    lambda e: self.app.navigate_to("analytics"),
                ),
            ],
            spacing=16,
        )

        content = ft.Column(
            [
                AppTheme.page_header(
                    "Dashboard",
                    f"Bienvenido, {Session.get_email()}",
                    c,
                ),
                ft.Container(height=24),
                stat_row,
                ft.Container(height=24),
                ft.Text("Acciones rápidas", size=15, weight=ft.FontWeight.W_600, color=c["text"]),
                ft.Container(height=12),
                quick_actions,
                ft.Container(height=24),
                ft.Text("Ventas recientes", size=15, weight=ft.FontWeight.W_600, color=c["text"]),
                ft.Container(height=12),
                recent_table,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        return ft.Container(
            content=content,
            expand=True,
            padding=ft.padding.all(28),
            bgcolor=c["bg"],
        )

    # ─── Recent sales table ───────────────────────────────────────
    def _build_recent_sales(self, sales):
        c = self.colors
        if not sales:
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.RECEIPT_LONG_ROUNDED, color=c["text_secondary"], size=48),
                        ft.Text("Sin ventas aún", color=c["text_secondary"], size=14),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.alignment.center,
                height=120,
                bgcolor=c["card"],
                border_radius=16,
                border=ft.border.all(1, c["border"]),
            )

        rows = []
        for sale in sales:
            total   = float(sale.get("total", 0))
            created = str(sale.get("created_at", ""))[:16].replace("T", " ")
            status  = sale.get("status", "completed")
            status_color = AppTheme.SUCCESS if status == "completed" else AppTheme.WARNING

            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(sale.get("id", ""))[:8] + "...", size=12, color=c["text"])),
                        ft.DataCell(ft.Text(created, size=12, color=c["text"])),
                        ft.DataCell(ft.Text(f"${total:,.2f}", size=13, weight=ft.FontWeight.W_600, color=c["text"])),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(status, size=11, color="white"),
                                bgcolor=status_color,
                                border_radius=20,
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                            )
                        ),
                    ]
                )
            )

        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID",     size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Fecha",  size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Total",  size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600)),
                ft.DataColumn(ft.Text("Estado", size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600)),
            ],
            rows=rows,
            border=ft.border.all(0, "transparent"),
            heading_row_color=c["surface"],
            data_row_min_height=48,
            column_spacing=20,
            horizontal_lines=ft.border.BorderSide(1, c["divider"]),
        )

        return ft.Container(
            content=ft.Column([table], scroll=ft.ScrollMode.AUTO),
            bgcolor=c["card"],
            border_radius=16,
            border=ft.border.all(1, c["border"]),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    # ─── Quick action card ────────────────────────────────────────
    def _quick_action(self, label, icon, gradient, on_click):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(icon, color="white", size=28),
                        width=56, height=56, border_radius=16,
                        gradient=gradient,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(label, size=13, color=self.colors["text"], weight=ft.FontWeight.W_500),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
            width=140,
            padding=ft.padding.symmetric(vertical=20, horizontal=16),
            bgcolor=self.colors["card"],
            border_radius=16,
            border=ft.border.all(1, self.colors["border"]),
            on_click=on_click,
            ink=True,
            alignment=ft.alignment.center,
        )