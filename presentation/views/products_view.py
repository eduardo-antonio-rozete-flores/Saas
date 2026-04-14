# presentation/views/products_view.py

import flet as ft
from presentation.theme import AppTheme


class ProductsView:

    def __init__(self, page, colors, is_dark, product_controller, category_controller, app):
        self.page = page
        self.colors = colors
        self.is_dark = is_dark
        self.product_ctrl = product_controller
        self.category_ctrl = category_controller
        self.app = app

        self._products: list[dict] = []
        self._categories: list[dict] = []
        self._table_rows = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

    # ─────────────────────────────────────────────────────────────
    def build(self):
        self._products = self.product_ctrl.get_products()
        self._categories = self.category_ctrl.get_categories()
        self._render_rows()

        search = AppTheme.make_text_field("Buscar producto...", colors=self.colors)
        search.expand = True
        search.prefix_icon = ft.icons.SEARCH_ROUNDED
        search.on_change = lambda e: self._filter(e.control.value)

        add_btn = ft.Container(
            content=ft.Row(
                [ft.Icon(ft.icons.ADD_ROUNDED, color="white", size=18),
                 ft.Text("Nuevo Producto", color="white", weight=ft.FontWeight.W_600)],
                spacing=6, tight=True,
            ),
            gradient=AppTheme.gradient_primary(),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=18, vertical=11),
            on_click=lambda e: self._show_form_dialog(),
            ink=True,
        )

        header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Productos", size=22, weight=ft.FontWeight.BOLD, color=self.colors["text"]),
                        ft.Text(f"{len(self._products)} productos registrados", size=13, color=self.colors["text_secondary"]),
                    ], spacing=2, tight=True, expand=True,
                ),
                add_btn,
            ],
        )

        col_header = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Nombre", size=12, color=self.colors["text_secondary"], weight=ft.FontWeight.W_600, expand=3),
                    ft.Text("Categoría", size=12, color=self.colors["text_secondary"], weight=ft.FontWeight.W_600, expand=2),
                    ft.Text("Precio", size=12, color=self.colors["text_secondary"], weight=ft.FontWeight.W_600, expand=1),
                    ft.Text("Costo", size=12, color=self.colors["text_secondary"], weight=ft.FontWeight.W_600, expand=1),
                    ft.Text("Acciones", size=12, color=self.colors["text_secondary"], weight=ft.FontWeight.W_600, width=100),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=self.colors["surface"],
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
        )

        table_container = ft.Container(
            content=ft.Column(
                [col_header, ft.Container(height=1, bgcolor=self.colors["border"]), self._table_rows],
                spacing=0, expand=True,
            ),
            bgcolor=self.colors["card"],
            border_radius=12,
            border=ft.border.all(1, self.colors["border"]),
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        return ft.Container(
            content=ft.Column(
                [header, ft.Container(height=8), search, ft.Container(height=12), table_container],
                spacing=8, expand=True,
            ),
            expand=True,
            padding=ft.padding.all(28),
            bgcolor=self.colors["bg"],
        )

    # ─── Render rows ──────────────────────────────────────────────
    def _render_rows(self, products=None):
        c = self.colors
        data = products if products is not None else self._products
        self._table_rows.controls.clear()

        if not data:
            self._table_rows.controls.append(
                ft.Container(
                    content=ft.Column(
                        [ft.Icon(ft.icons.INVENTORY_2_ROUNDED, color=c["text_secondary"], size=48),
                         ft.Text("Sin productos", color=c["text_secondary"])],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
                    ),
                    alignment=ft.alignment.center, height=160,
                )
            )
            return

        for p in data:
            name = p.get("name", "")
            price = float(p.get("price") or 0)
            cost = float(p.get("cost") or 0)
            category = (p.get("categories") or {}).get("name", "—")

            row = ft.Container(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Icon(ft.icons.INVENTORY_2_ROUNDED, color=AppTheme.ACCENT, size=16),
                                    width=32, height=32, border_radius=8,
                                    bgcolor=f"{AppTheme.ACCENT}18", alignment=ft.alignment.center,
                                ),
                                ft.Text(name, size=13, color=c["text"], weight=ft.FontWeight.W_500,
                                        expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            expand=3, spacing=10,
                        ),
                        ft.Container(
                            content=ft.Text(category, size=12, color="white"),
                            bgcolor=f"{AppTheme.ACCENT}80", border_radius=20,
                            padding=ft.padding.symmetric(horizontal=10, vertical=3),
                            expand=2,
                        ),
                        ft.Text(f"${price:,.2f}", size=13, color=c["text"], weight=ft.FontWeight.W_600, expand=1),
                        ft.Text(f"${cost:,.2f}", size=12, color=c["text_secondary"], expand=1),
                        ft.Row(
                            [
                                ft.IconButton(
                                    ft.icons.EDIT_ROUNDED, icon_size=16, icon_color=AppTheme.ACCENT,
                                    tooltip="Editar",
                                    on_click=lambda e, prod=p: self._show_form_dialog(prod),
                                    style=ft.ButtonStyle(padding=ft.padding.all(4)),
                                ),
                                ft.IconButton(
                                    ft.icons.DELETE_ROUNDED, icon_size=16, icon_color=AppTheme.ERROR,
                                    tooltip="Eliminar",
                                    on_click=lambda e, pid=p["id"]: self._confirm_delete(pid),
                                    style=ft.ButtonStyle(padding=ft.padding.all(4)),
                                ),
                            ],
                            spacing=0, width=100,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor="transparent",
                border=ft.border.only(bottom=ft.border.BorderSide(1, c["divider"])),
                on_hover=lambda e, row_ctrl=None: None,
            )
            self._table_rows.controls.append(row)

        self.page.update()

    def _filter(self, query: str):
        q = query.lower().strip()
        if q:
            filtered = [p for p in self._products if q in p.get("name", "").lower()]
        else:
            filtered = list(self._products)
        self._render_rows(filtered)

    # ─── Form dialog ──────────────────────────────────────────────
    def _show_form_dialog(self, product: dict | None = None):
        c = self.colors
        is_edit = product is not None
        title_text = "Editar Producto" if is_edit else "Nuevo Producto"

        name_f = AppTheme.make_text_field("Nombre *", colors=c, value=product.get("name", "") if is_edit else "")
        price_f = AppTheme.make_text_field("Precio *", colors=c, value=str(product.get("price", "")) if is_edit else "")
        cost_f = AppTheme.make_text_field("Costo", colors=c, value=str(product.get("cost", "")) if is_edit else "")
        sku_f = AppTheme.make_text_field("SKU", colors=c, value=product.get("sku", "") if is_edit else "")

        cat_options = [ft.dropdown.Option(key="", text="Sin categoría")]
        for cat in self._categories:
            cat_options.append(ft.dropdown.Option(key=cat["id"], text=cat["name"]))

        cat_dd = ft.Dropdown(
            options=cat_options,
            value=(product.get("category_id") or "") if is_edit else "",
            border_radius=12,
            border_color=c["border"],
            focused_border_color=AppTheme.ACCENT,
            label="Categoría",
            label_style=ft.TextStyle(color=c["text_secondary"], size=13),
            text_style=ft.TextStyle(color=c["text"]),
            bgcolor=c["input_fill"],
        )

        def on_save(e):
            data = {
                "name": name_f.value or "",
                "price": price_f.value or "0",
                "cost": cost_f.value or "0",
                "sku": sku_f.value or "",
                "category_id": cat_dd.value or None,
            }
            if is_edit and product is not None:
                ok = self.product_ctrl.update_product(product["id"], data)
            else:
                ok = self.product_ctrl.create_product(data)

            if ok:
                dialog.open = False
                self.page.update()
                self._products = self.product_ctrl.get_products()
                self._render_rows()

        def on_cancel(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title_text, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [name_f, ft.Row([price_f, cost_f], spacing=10), sku_f, cat_dd],
                    spacing=12, tight=True,
                ),
                width=360,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=on_cancel),
                ft.Container(
                    content=ft.Text("Guardar", color="white", weight=ft.FontWeight.W_600),
                    gradient=AppTheme.gradient_primary(),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    on_click=on_save, ink=True,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    # ─── Delete confirm ───────────────────────────────────────────
    def _confirm_delete(self, product_id: str):
        def do_delete(e):
            dialog.open = False
            self.page.update()
            ok = self.product_ctrl.delete_product(product_id)
            if ok:
                self._products = self.product_ctrl.get_products()
                self._render_rows()

        def cancel(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([ft.Icon(ft.icons.WARNING_ROUNDED, color=AppTheme.ERROR),
                          ft.Text("Eliminar Producto", weight=ft.FontWeight.BOLD)], spacing=8),
            content=ft.Text("¿Estás seguro? Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.Container(
                    content=ft.Text("Eliminar", color="white", weight=ft.FontWeight.W_600),
                    gradient=AppTheme.gradient_error(),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    on_click=do_delete, ink=True,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()