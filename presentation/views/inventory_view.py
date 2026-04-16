# presentation/views/inventory_view.py
#
# NUEVA — Fase 5: Inventario Inteligente
#
# LAYOUT:
#   ┌─────────────────────────────────────────────────────────┐
#   │ 📦 Inventario               [🔴 N alertas] [🔄 Refresh] │
#   ├─────────────────────────────────────────────────────────┤
#   │ [!] Banner de stock bajo (si hay alertas)               │
#   ├──────────┬──────────┬────────┬───────┬──────────────────┤
#   │ Producto │   SKU    │ Stock  │ Mín.  │    Acciones      │
#   ├──────────┼──────────┼────────┼───────┼──────────────────┤
#   │  ...     │  ...     │  ...   │  ...  │ [Ajustar][Kardex]│
#   └──────────┴──────────┴────────┴───────┴──────────────────┘
#
# PATRÓN:
#   Recibe inventory_controller inyectado.
#   No llama a repositorios ni servicios directamente.
#   Estados vacíos elegantes en todos los casos.

from __future__ import annotations
import flet as ft
from presentation.theme import AppTheme


class InventoryView:

    def __init__(self, page, colors, is_dark, inventory_controller, app):
        self.page    = page
        self.colors  = colors
        self.is_dark = is_dark
        self.ctrl    = inventory_controller
        self.app     = app
        self._inventory: list[dict] = []
        self._rows_col = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    # ================================================================== #
    # Build                                                               #
    # ================================================================== #
    def build(self):
        c = self.colors
        self._inventory = self.ctrl.get_inventory()
        alerts          = self.ctrl.get_low_stock_alerts()

        self._render_rows()

        refresh_btn = ft.IconButton(
            ft.icons.REFRESH_ROUNDED,
            icon_color=AppTheme.ACCENT,
            tooltip="Actualizar inventario",
            on_click=self._refresh,
        )

        # Banner de alertas (visible solo si hay stock bajo)
        alert_banner = self._build_alert_banner(alerts) if alerts else ft.Container(height=0)

        col_header = ft.Container(
            content=ft.Row([
                ft.Text("Producto",  size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600, expand=3),
                ft.Text("Barcode",   size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600, expand=2),
                ft.Text("Stock",     size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600, expand=1),
                ft.Text("Mínimo",    size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600, expand=1),
                ft.Text("Estado",    size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600, expand=1),
                ft.Text("Acciones",  size=12, color=c["text_secondary"], weight=ft.FontWeight.W_600, width=120),
            ]),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=c["surface"],
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
        )

        table = ft.Container(
            content=ft.Column(
                [col_header, ft.Container(height=1, bgcolor=c["border"]), self._rows_col],
                spacing=0, expand=True,
            ),
            bgcolor=c["card"],
            border_radius=12,
            border=ft.border.all(1, c["border"]),
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        return ft.Container(
            content=ft.Column([
                AppTheme.page_header(
                    "Inventario",
                    f"{len(self._inventory)} productos registrados",
                    c,
                    action=refresh_btn,
                ),
                ft.Container(height=16),
                alert_banner,
                ft.Container(height=8) if alerts else ft.Container(height=0),
                table,
            ], expand=True),
            expand=True,
            padding=ft.padding.all(28),
            bgcolor=c["bg"],
        )

    # ================================================================== #
    # Banner de stock bajo                                               #
    # ================================================================== #
    def _build_alert_banner(self, alerts: list) -> ft.Container:
        c = self.colors
        items_text = ", ".join(
            f"{a['product_name']} ({a['stock_actual']}/{a['stock_minimo']})"
            for a in alerts[:3]
        )
        extra = f" y {len(alerts) - 3} más" if len(alerts) > 3 else ""

        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="white", size=20),
                ft.Column([
                    ft.Text(
                        f"⚠️  {len(alerts)} producto(s) con stock bajo",
                        color="white", size=13, weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        f"{items_text}{extra}",
                        color="white", size=11, opacity=0.9,
                    ),
                ], spacing=2, tight=True, expand=True),
            ], spacing=12),
            bgcolor=AppTheme.WARNING,
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

    # ================================================================== #
    # Render rows                                                         #
    # ================================================================== #
    def _render_rows(self, inventory: list = None): #type: ignore
        c    = self.colors
        data = inventory if inventory is not None else self._inventory
        self._rows_col.controls.clear()

        if not data:
            self._rows_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.INVENTORY_ROUNDED, color=c["text_secondary"], size=48),
                        ft.Text("Sin inventario registrado", color=c["text_secondary"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    alignment=ft.alignment.center, height=160,
                )
            )
            self.page.update()
            return

        for item in data:
            product   = item.get("products") or {}
            name      = product.get("name", "—")
            barcode   = product.get("barcode") or "—"
            stock_act = item.get("stock_actual", 0)
            stock_min = item.get("stock_minimo", 0)
            product_id = product.get("id", "")
            is_low     = stock_act <= stock_min

            # Color del chip de estado
            if stock_act == 0:
                status_text  = "Agotado"
                status_color = AppTheme.ERROR
            elif is_low:
                status_text  = "Bajo"
                status_color = AppTheme.WARNING
            else:
                status_text  = "OK"
                status_color = AppTheme.SUCCESS

            row = ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.icons.INVENTORY_2_ROUNDED,
                                            color=AppTheme.ACCENT, size=16),
                            width=30, height=30, border_radius=7,
                            bgcolor=f"{AppTheme.ACCENT}18",
                            alignment=ft.alignment.center,
                        ),
                        ft.Text(name, size=13, color=c["text"], expand=True,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ], expand=3, spacing=8),

                    ft.Text(barcode, size=11, color=c["text_secondary"],
                            font_family="monospace", expand=2,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),

                    # Stock actual — resaltado si es bajo
                    ft.Text(
                        str(stock_act),
                        size=14, weight=ft.FontWeight.BOLD,
                        color=AppTheme.ERROR if is_low else c["text"],
                        expand=1,
                    ),
                    ft.Text(str(stock_min), size=13, color=c["text_secondary"], expand=1),

                    # Badge de estado
                    ft.Container(
                        content=ft.Text(status_text, size=11, color="white"),
                        bgcolor=status_color,
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=10, vertical=3),
                        expand=1,
                    ),

                    # Acciones
                    ft.Row([
                        ft.IconButton(
                            ft.icons.EDIT_NOTE_ROUNDED,
                            icon_size=16, icon_color=AppTheme.ACCENT,
                            tooltip="Ajustar stock",
                            on_click=lambda e, pid=product_id, n=name,
                                            sa=stock_act, sm=stock_min:
                                self._show_adjust_dialog(pid, n, sa, sm),
                            style=ft.ButtonStyle(padding=ft.padding.all(4)),
                        ),
                        ft.IconButton(
                            ft.icons.HISTORY_ROUNDED,
                            icon_size=16, icon_color=AppTheme.BLUE,
                            tooltip="Ver kardex",
                            on_click=lambda e, pid=product_id, n=name:
                                self._show_kardex_dialog(pid, n),
                            style=ft.ButtonStyle(padding=ft.padding.all(4)),
                        ),
                    ], spacing=0, width=120),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=f"{AppTheme.WARNING}08" if is_low else "transparent",
                border=ft.border.only(
                    bottom=ft.border.BorderSide(1, c["divider"]),
                    left=ft.border.BorderSide(3, AppTheme.WARNING if is_low else "transparent"),
                ),
            )
            self._rows_col.controls.append(row)

        self.page.update()

    # ================================================================== #
    # Dialog: Ajustar stock                                              #
    # ================================================================== #
    def _show_adjust_dialog(self, product_id: str, name: str,
                            stock_actual: int, stock_minimo: int):
        c = self.colors

        stock_f = AppTheme.make_text_field(
            "Nuevo stock *", colors=c, value=str(stock_actual)
        )
        minimo_f = AppTheme.make_text_field(
            "Stock mínimo", colors=c, value=str(stock_minimo)
        )
        notas_f = AppTheme.make_text_field(
            "Motivo del ajuste", colors=c,
        )

        def on_save(e):
            try:
                nuevo = int(stock_f.value or 0)
                minimo = int(minimo_f.value or stock_minimo)
            except ValueError:
                self.app.show_snackbar("Valores numéricos inválidos", error=True)
                return

            ok = self.ctrl.adjust_stock(
                product_id, nuevo, minimo, notas_f.value or ""
            )
            if ok:
                dialog.open = False
                self.page.update()
                # Refrescar vista
                self._inventory = self.ctrl.get_inventory()
                self._render_rows()

        def on_cancel(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.EDIT_NOTE_ROUNDED, color=AppTheme.ACCENT),
                ft.Text(f"Ajustar Stock — {name}", weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Stock actual:", size=13, color=c["text_secondary"]),
                            ft.Text(str(stock_actual), size=18,
                                    weight=ft.FontWeight.BOLD, color=c["text"]),
                        ], spacing=8),
                        padding=ft.padding.symmetric(vertical=8),
                    ),
                    ft.Row([stock_f, minimo_f], spacing=10),
                    notas_f,
                ], spacing=10, tight=True),
                width=380,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=on_cancel),
                ft.Container(
                    content=ft.Text("Guardar", color="white", weight=ft.FontWeight.W_600),
                    gradient=AppTheme.gradient_primary(), border_radius=8,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    on_click=on_save, ink=True,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    # ================================================================== #
    # Dialog: Kardex (historial de movimientos)                         #
    # ================================================================== #
    def _show_kardex_dialog(self, product_id: str, product_name: str):
        c       = self.colors
        entries = self.ctrl.get_kardex(product_id, limit=30)

        if not entries:
            rows_content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.HISTORY_ROUNDED, color=c["text_secondary"], size=36),
                    ft.Text("Sin movimientos registrados", color=c["text_secondary"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                alignment=ft.alignment.center, height=120,
            )
        else:
            TIPO_COLORS = {
                "entrada": AppTheme.SUCCESS,
                "salida":  AppTheme.ERROR,
                "ajuste":  AppTheme.WARNING,
                "inicio":  AppTheme.ACCENT,
            }
            TIPO_ICONS = {
                "entrada": ft.icons.ARROW_DOWNWARD_ROUNDED,
                "salida":  ft.icons.ARROW_UPWARD_ROUNDED,
                "ajuste":  ft.icons.SWAP_VERT_ROUNDED,
                "inicio":  ft.icons.FIBER_NEW_ROUNDED,
            }

            kardex_rows = []
            for entry in entries:
                tipo      = entry.get("tipo", "—")
                cantidad  = entry.get("cantidad", 0)
                saldo_ant = entry.get("saldo_anterior", 0)
                saldo_pos = entry.get("saldo_posterior", 0)
                fecha     = str(entry.get("created_at", ""))[:16].replace("T", " ")
                notas     = entry.get("notas") or entry.get("referencia_tipo") or "—"
                color     = TIPO_COLORS.get(tipo, c["text_secondary"])
                icon      = TIPO_ICONS.get(tipo, ft.icons.CIRCLE_ROUNDED)

                kardex_rows.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(icon, color="white", size=14),
                                width=26, height=26, border_radius=6,
                                bgcolor=color, alignment=ft.alignment.center,
                            ),
                            ft.Column([
                                ft.Text(notas, size=11, color=c["text"],
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(fecha, size=10, color=c["text_secondary"]),
                            ], spacing=1, tight=True, expand=True),
                            ft.Column([
                                ft.Text(
                                    f"{'+' if cantidad > 0 else ''}{cantidad}",
                                    size=12, weight=ft.FontWeight.BOLD,
                                    color=AppTheme.SUCCESS if cantidad > 0 else AppTheme.ERROR,
                                ),
                                ft.Text(
                                    f"{saldo_ant} → {saldo_pos}",
                                    size=10, color=c["text_secondary"],
                                ),
                            ], spacing=1, tight=True,
                               horizontal_alignment=ft.CrossAxisAlignment.END),
                        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(horizontal=10, vertical=8),
                        border=ft.border.only(bottom=ft.border.BorderSide(1, c["divider"])),
                    )
                )

            rows_content = ft.Container(
                content=ft.Column(kardex_rows, spacing=0, scroll=ft.ScrollMode.AUTO),
                height=360,
            )

        def close(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.HISTORY_ROUNDED, color=AppTheme.BLUE),
                ft.Text(f"Kardex — {product_name}", weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(content=rows_content, width=440),
            actions=[
                ft.Container(
                    content=ft.Text("Cerrar", color="white", weight=ft.FontWeight.W_600),
                    gradient=AppTheme.gradient_primary(), border_radius=8,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    on_click=close, ink=True,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _refresh(self, e):
        self.app.navigate_to("inventory")