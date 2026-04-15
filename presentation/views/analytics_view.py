# presentation/views/analytics_view.py
#
# JUSTIFICACIÓN ARQUITECTÓNICA:
# Esta vista vive en 'presentation' y es puramente de UI.
# Recibe analytics_controller ya construido (DI desde app.py).
# No llama directamente a repositorios ni servicios.
#
# DECISIONES DE DISEÑO UI:
# • Dos gráficas principales: LineChart (ventas por día) y BarChart (top productos).
#   Se usan los componentes nativos de Flet para máximo rendimiento y consistencia
#   con el tema de la app (sin dependencias externas como matplotlib).
# • Tarjetas KPI en la parte superior: ingresos totales, ticket promedio,
#   crecimiento y ventas hoy. Mismo patrón visual que dashboard_view.py
#   (stat_card de AppTheme) para cohesión visual.
# • Si no hay datos suficientes se muestran estados vacíos elegantes,
#   nunca un crash ni una pantalla en blanco.
# • Botón de refresh manual (icono en header) para recargar sin cambiar de vista.
#
# PATRÓN SEGUIDO:
# Igual que DashboardView / SalesView: __init__ recibe dependencias,
# build() construye y devuelve el árbol de controles Flet.

from __future__ import annotations

import flet as ft
from presentation.theme import AppTheme


class AnalyticsView:

    def __init__(self, page, colors, is_dark, analytics_controller, app):
        self.page                = page
        self.colors              = colors
        self.is_dark             = is_dark
        self.analytics_ctrl      = analytics_controller
        self.app                 = app
        self._data: dict         = {}

    # ================================================================== #
    # Punto de entrada                                                    #
    # ================================================================== #
    def build(self):
        self._data = self.analytics_ctrl.get_dashboard()

        refresh_btn = ft.IconButton(
            ft.icons.REFRESH_ROUNDED,
            icon_color=AppTheme.ACCENT,
            tooltip="Actualizar métricas",
            on_click=self._refresh,
        )

        return ft.Container(
            content=ft.Column(
                [
                    AppTheme.page_header(
                        "Analytics",
                        "Métricas de negocio en tiempo real",
                        self.colors,
                        action=refresh_btn,
                    ),
                    ft.Container(height=20),
                    self._build_kpi_row(),
                    ft.Container(height=24),
                    self._build_charts_row(),
                    ft.Container(height=24),
                    self._build_top_products_section(),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.all(28),
            bgcolor=self.colors["bg"],
        )

    # ================================================================== #
    # KPI Cards                                                          #
    # ================================================================== #
    def _build_kpi_row(self):
        d = self._data
        growth = d.get("growth_rate", 0)
        growth_color = AppTheme.SUCCESS if growth >= 0 else AppTheme.ERROR
        growth_icon  = (
            ft.icons.TRENDING_UP_ROUNDED   if growth >= 0
            else ft.icons.TRENDING_DOWN_ROUNDED
        )

        cards = [
            self._kpi_card(
                "Ingresos Totales",
                f"${d.get('total_revenue', 0):,.2f}",
                ft.icons.ATTACH_MONEY_ROUNDED,
                AppTheme.gradient_success(),
                subtitle="ventas completadas",
            ),
            self._kpi_card(
                "Ticket Promedio",
                f"${d.get('avg_ticket', 0):,.2f}",
                ft.icons.RECEIPT_ROUNDED,
                AppTheme.gradient_primary(),
                subtitle="por venta",
            ),
            self._kpi_card(
                "Crecimiento",
                f"{growth:+.1f}%",
                growth_icon,
                AppTheme.gradient_warning() if growth >= 0 else AppTheme.gradient_error(),
                subtitle="primer → último día",
                value_color=growth_color,
            ),
            self._kpi_card(
                "Ventas Hoy",
                str(d.get("sales_today", 0)),
                ft.icons.TODAY_ROUNDED,
                AppTheme.gradient_info(),
                subtitle="transacciones",
            ),
        ]
        return ft.Row(cards, spacing=14)

    def _kpi_card(self, title, value, icon, gradient, subtitle="", value_color=None):
        c = self.colors
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(icon, color="white", size=22),
                                width=44,
                                height=44,
                                border_radius=12,
                                gradient=gradient,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        title,
                                        size=11,
                                        color=c["text_secondary"],
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        value,
                                        size=22,
                                        weight=ft.FontWeight.BOLD,
                                        color=value_color or c["text"],
                                    ),
                                ],
                                spacing=1,
                                tight=True,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Text(subtitle, size=11, color=c["text_secondary"]),
                ],
                spacing=8,
                tight=True,
            ),
            padding=ft.padding.all(18),
            bgcolor=c["card"],
            border_radius=16,
            border=ft.border.all(1, c["border"]),
            expand=True,
        )

    # ================================================================== #
    # Fila de gráficas: LineChart ventas por día                         #
    # ================================================================== #
    def _build_charts_row(self):
        return ft.Row(
            [
                self._build_sales_line_chart(),
            ],
            spacing=16,
        )

    def _build_sales_line_chart(self):
        c          = self.colors
        sales_data = self._data.get("sales_by_day", [])

        # ── Estado vacío ──────────────────────────────────────────────
        if not sales_data:
            return self._empty_chart_card(
                "Ventas por Día",
                "Aún no hay ventas registradas.\nRealiza tu primera venta en el POS.",
                ft.icons.SHOW_CHART_ROUNDED,
            )

        # ── Normalización de puntos ───────────────────────────────────
        totals    = [float(r.get("total", 0)) for r in sales_data]
        max_total = max(totals) if totals else 1
        min_total = min(totals) if totals else 0

        data_points = [
            ft.LineChartDataPoint(x=float(i), y=float(v))
            for i, v in enumerate(totals)
        ]

        # Etiquetas del eje X (fechas abreviadas)
        def short_date(row):
            d = str(row.get("day", ""))
            # d puede venir como "2025-04-10" o similar
            parts = d.split("-")
            if len(parts) >= 3:
                return f"{parts[2]}/{parts[1]}"
            return d[-5:]

        x_labels = [
            ft.ChartAxisLabel(
                value=float(i),
                label=ft.Text(
                    short_date(sales_data[i]),
                    size=9,
                    color=c["text_secondary"],
                ),
            )
            for i in range(0, len(sales_data), max(1, len(sales_data) // 6))
        ]

        # Etiquetas del eje Y (montos)
        def fmt_money(v):
            if v >= 1000:
                return f"${v/1000:.1f}k"
            return f"${v:.0f}"

        y_steps  = 5
        y_step   = (max_total - min_total) / y_steps if max_total != min_total else 1
        y_labels = [
            ft.ChartAxisLabel(
                value=min_total + y_step * i,
                label=ft.Text(
                    fmt_money(min_total + y_step * i),
                    size=9,
                    color=c["text_secondary"],
                ),
            )
            for i in range(y_steps + 1)
        ]

        line_chart = ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=data_points,
                    color=AppTheme.ACCENT,
                    curved=True,
                    stroke_width=2.5,
                    stroke_cap_round=True,
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=[f"{AppTheme.ACCENT}55", f"{AppTheme.ACCENT}00"],
                    ),
                    point=ft.ChartCirclePoint(radius=3, color=AppTheme.ACCENT),
                )
            ],
            left_axis=ft.ChartAxis(
                labels=y_labels,
                labels_size=46,
            ),
            bottom_axis=ft.ChartAxis(
                labels=x_labels,
                labels_size=28,
            ),
            border=ft.Border(
                bottom=ft.BorderSide(1, c["divider"]),
                left=ft.BorderSide(1, c["divider"]),
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=c["divider"],
                dash_pattern=[4, 4],
                width=1,
            ),
            min_y=min_total * 0.9,
            max_y=max_total * 1.1,
            min_x=0,
            max_x=float(max(len(sales_data) - 1, 1)),
            expand=True,
            tooltip_bgcolor=c["card"],
            interactive=True,
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.SHOW_CHART_ROUNDED, color=AppTheme.ACCENT, size=18),
                            ft.Text(
                                "Ventas por Día",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=c["text"],
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                f"{len(sales_data)} días",
                                size=11,
                                color=c["text_secondary"],
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        content=line_chart,
                        height=220,
                        expand=True,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(20),
            bgcolor=c["card"],
            border_radius=16,
            border=ft.border.all(1, c["border"]),
            expand=True,
        )

    # ================================================================== #
    # Top productos — BarChart                                           #
    # ================================================================== #
    def _build_top_products_section(self):
        c        = self.colors
        top_data = self._data.get("top_products", [])

        if not top_data:
            return self._empty_chart_card(
                "Top Productos",
                "Sin datos de productos vendidos aún.",
                ft.icons.BAR_CHART_ROUNDED,
            )

        # Limitamos a top 8 para no saturar el gráfico
        top_data  = top_data[:8]
        max_qty   = max(int(r.get("total_qty", 0)) for r in top_data) or 1

        bar_groups = [
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=float(row.get("total_qty", 0)),
                        width=28,
                        color=self._bar_color(i),
                        border_radius=ft.border_radius.only(top_left=6, top_right=6),
                        tooltip=f"{row.get('name', '')} · {row.get('total_qty', 0)} uds.",
                    )
                ],
            )
            for i, row in enumerate(top_data)
        ]

        bar_chart = ft.BarChart(
            bar_groups=bar_groups,
            border=ft.Border(
                bottom=ft.BorderSide(1, c["divider"]),
                left=ft.BorderSide(1, c["divider"]),
            ),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=float(v),
                        label=ft.Text(str(v), size=9, color=c["text_secondary"]),
                    )
                    for v in range(0, int(max_qty) + 1, max(1, int(max_qty) // 5))
                ],
                labels_size=32,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=float(i),
                        label=ft.Container(
                            content=ft.Text(
                                self._truncate(row.get("name", ""), 10),
                                size=9,
                                color=c["text_secondary"],
                                text_align=ft.TextAlign.CENTER,
                            ),
                            width=48,
                        ),
                    )
                    for i, row in enumerate(top_data)
                ],
                labels_size=32,
            ),
            horizontal_grid_lines=ft.ChartGridLines(
                color=c["divider"],
                dash_pattern=[4, 4],
                width=1,
            ),
            max_y=max_qty * 1.15,
            interactive=True,
            tooltip_bgcolor=c["card"],
            expand=True,
        )

        # Leyenda / tabla de productos al lado del gráfico
        legend_rows = [
            ft.Row(
                [
                    ft.Container(
                        width=10,
                        height=10,
                        border_radius=3,
                        bgcolor=self._bar_color(i),
                    ),
                    ft.Text(
                        row.get("name", ""),
                        size=12,
                        color=c["text"],
                        expand=True,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Text(
                        f"{row.get('total_qty', 0)} uds.",
                        size=12,
                        color=c["text_secondary"],
                        weight=ft.FontWeight.W_600,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            for i, row in enumerate(top_data)
        ]

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.BAR_CHART_ROUNDED, color=AppTheme.SUCCESS, size=18),
                            ft.Text(
                                "Top Productos",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=c["text"],
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Container(height=16),
                    ft.Row(
                        [
                            ft.Container(content=bar_chart, expand=3, height=240),
                            ft.Container(width=24),
                            ft.Column(
                                legend_rows,
                                spacing=10,
                                expand=2,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(20),
            bgcolor=c["card"],
            border_radius=16,
            border=ft.border.all(1, c["border"]),
        )

    # ================================================================== #
    # Helpers                                                             #
    # ================================================================== #
    def _empty_chart_card(self, title: str, message: str, icon):
        c = self.colors
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=AppTheme.ACCENT, size=18),
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=c["text"]),
                        ],
                        spacing=8,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Icon(icon, color=c["text_secondary"], size=48, opacity=0.4),
                                ft.Text(
                                    message,
                                    color=c["text_secondary"],
                                    size=13,
                                    text_align=ft.TextAlign.CENTER,
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        alignment=ft.alignment.center,
                        height=200,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.padding.all(20),
            bgcolor=c["card"],
            border_radius=16,
            border=ft.border.all(1, c["border"]),
            expand=True,
        )

    # Colores rotativos para las barras del top productos
    _BAR_COLORS = [
        AppTheme.ACCENT,
        AppTheme.SUCCESS,
        AppTheme.WARNING,
        AppTheme.PINK,
        AppTheme.BLUE,
        AppTheme.ERROR,
        "#A78BFA",
        "#34D399",
    ]

    def _bar_color(self, idx: int) -> str:
        return self._BAR_COLORS[idx % len(self._BAR_COLORS)]

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        return text if len(text) <= max_len else text[:max_len - 1] + "…"

    # ================================================================== #
    # Refresh                                                             #
    # ================================================================== #
    def _refresh(self, e):
        """
        Recarga los datos y reconstruye la vista.
        DECISIÓN: en lugar de hacer update parcial de controles,
        pedimos a app.navigate_to("analytics") para reconstruir
        la vista completa. Esto es más simple y garantiza coherencia.
        """
        self.app.navigate_to("analytics")