# presentation/views/pos_view.py

import flet as ft
from presentation.theme import AppTheme


class PosView:

    def __init__(self, page, colors, is_dark, sale_controller, product_controller, app):
        self.page = page
        self.colors = colors
        self.is_dark = is_dark
        self.sale_controller = sale_controller
        self.product_controller = product_controller
        self.app = app

        self.cart: list[dict] = []
        self.all_products: list[dict] = []
        self.filtered_products: list[dict] = []

        # Mutable UI refs
        self._cart_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, expand=True)
        self._total_text = ft.Text("$0.00", size=26, weight=ft.FontWeight.BOLD, color="white")
        self._subtotal_text = ft.Text("Subtotal: $0.00", size=13)
        self._item_count_text = ft.Text("0 ítems", size=12)
        self._product_grid = ft.GridView(
            expand=True,
            runs_count=3,
            max_extent=170,
            spacing=10,
            run_spacing=10,
        )
        self._search_field = AppTheme.make_text_field(
            "Buscar producto...", colors=colors, width=None
        )
        self._search_field.expand = True

    # ─────────────────────────────────────────────────────────────
    def build(self):
        self._load_products()

        self._search_field.on_change = self._on_search
        self._search_field.prefix_icon = ft.icons.SEARCH_ROUNDED

        search_row = ft.Row(
            [self._search_field],
            spacing=10,
        )

        # Left panel – products
        left_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Productos",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=self.colors["text"],
                    ),
                    ft.Container(height=10),
                    search_row,
                    ft.Container(height=10),
                    self._product_grid,
                ],
                expand=True,
            ),
            expand=True,
            padding=ft.padding.all(20),
            bgcolor=self.colors["bg"],
        )

        # Right panel – cart
        right_panel = self._build_cart_panel()

        return ft.Row(
            [
                left_panel,
                ft.Container(width=1, bgcolor=self.colors["border"]),
                right_panel,
            ],
            expand=True,
            spacing=0,
        )

    # ─── Products ────────────────────────────────────────────────
    def _load_products(self):
        self.all_products = self.product_controller.get_products()
        self.filtered_products = list(self.all_products)
        self._render_products()

    def _on_search(self, e):
        q = (self._search_field.value or "").lower().strip()
        if q:
            self.filtered_products = [
                p for p in self.all_products if q in p.get("name", "").lower()
            ]
        else:
            self.filtered_products = list(self.all_products)
        self._render_products()

    def _render_products(self):
        self._product_grid.controls.clear()
        for p in self.filtered_products:
            self._product_grid.controls.append(self._product_card(p))
        self.page.update()

    def _product_card(self, product: dict):
        c = self.colors
        name = product.get("name", "")
        price = float(product.get("price", 0))
        category = (product.get("categories") or {}).get("name", "")

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.icons.INVENTORY_2_ROUNDED,
                            color=AppTheme.ACCENT,
                            size=28,
                        ),
                        width=48,
                        height=48,
                        border_radius=12,
                        bgcolor=f"{AppTheme.ACCENT}18",
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(
                        name,
                        size=13,
                        weight=ft.FontWeight.W_500,
                        color=c["text"],
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        category,
                        size=11,
                        color=c["text_secondary"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        f"${price:,.2f}",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=AppTheme.ACCENT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5,
            ),
            bgcolor=c["card"],
            border_radius=14,
            border=ft.border.all(1, c["border"]),
            padding=ft.padding.all(12),
            on_click=lambda e, prod=product: self._add_to_cart(prod),
            ink=True,
            alignment=ft.alignment.center,
        )

    # ─── Cart ────────────────────────────────────────────────────
    def _build_cart_panel(self):
        c = self.colors

        checkout_btn = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.SHOPPING_CART_CHECKOUT_ROUNDED, color="white", size=20),
                    ft.Column(
                        [
                            ft.Text("Cobrar", color="white", size=14, weight=ft.FontWeight.W_600),
                            self._total_text,
                        ],
                        spacing=0,
                        tight=True,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            gradient=AppTheme.gradient_primary(),
            border_radius=14,
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            on_click=self._show_checkout_dialog,
            ink=True,
        )

        clear_btn = ft.Container(
            content=ft.Row(
                [ft.Icon(ft.icons.DELETE_SWEEP_ROUNDED, color=AppTheme.ERROR, size=16),
                 ft.Text("Vaciar", color=AppTheme.ERROR, size=13)],
                spacing=6,
                tight=True,
            ),
            on_click=self._clear_cart,
            ink=True,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
        )

        header = ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("Carrito", size=16, weight=ft.FontWeight.BOLD, color=c["text"]),
                        self._item_count_text,
                    ],
                    spacing=2,
                    tight=True,
                    expand=True,
                ),
                clear_btn,
            ],
        )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=header,
                        padding=ft.padding.symmetric(horizontal=20, vertical=16),
                    ),
                    ft.Container(height=1, bgcolor=c["border"]),
                    ft.Container(
                        content=self._cart_col,
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=12, vertical=12),
                    ),
                    ft.Container(height=1, bgcolor=c["border"]),
                    ft.Container(
                        content=ft.Column(
                            [
                                self._subtotal_text,
                                ft.Container(height=8),
                                checkout_btn,
                            ]
                        ),
                        padding=ft.padding.all(16),
                    ),
                ],
                expand=True,
                spacing=0,
            ),
            width=300,
            bgcolor=c["card"],
        )

    def _add_to_cart(self, product: dict):
        pid = product["id"]
        for item in self.cart:
            if item["id"] == pid:
                item["quantity"] += 1
                item["subtotal"] = item["quantity"] * item["price"]
                self._refresh_cart()
                return

        self.cart.append(
            {
                "id": pid,
                "name": product.get("name", ""),
                "price": float(product.get("price", 0)),
                "quantity": 1,
                "subtotal": float(product.get("price", 0)),
            }
        )
        self._refresh_cart()

    def _remove_from_cart(self, product_id: str):
        self.cart = [i for i in self.cart if i["id"] != product_id]
        self._refresh_cart()

    def _update_quantity(self, product_id: str, delta: int):
        for item in self.cart:
            if item["id"] == product_id:
                item["quantity"] = max(1, item["quantity"] + delta)
                item["subtotal"] = item["quantity"] * item["price"]
        self._refresh_cart()

    def _clear_cart(self, e=None):
        self.cart.clear()
        self._refresh_cart()

    def _refresh_cart(self):
        c = self.colors
        self._cart_col.controls.clear()

        if not self.cart:
            self._cart_col.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.SHOPPING_CART_ROUNDED, color=c["text_secondary"], size=40),
                            ft.Text("El carrito está vacío", color=c["text_secondary"], size=13),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    alignment=ft.alignment.center,
                    expand=True,
                    padding=ft.padding.symmetric(vertical=40),
                )
            )
        else:
            for item in self.cart:
                self._cart_col.controls.append(self._cart_item_row(item))

        total = sum(i["subtotal"] for i in self.cart)
        count = sum(i["quantity"] for i in self.cart)
        self._total_text.value = f"${total:,.2f}"
        self._subtotal_text.value = f"Subtotal: ${total:,.2f}"
        self._item_count_text.value = f"{count} ítem{'s' if count != 1 else ''}"
        self._subtotal_text.color = self.colors["text_secondary"]
        self.page.update()

    def _cart_item_row(self, item: dict):
        c = self.colors
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                item["name"],
                                size=13,
                                weight=ft.FontWeight.W_500,
                                color=c["text"],
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                width=100,
                            ),
                            ft.Text(
                                f"${item['price']:,.2f} c/u",
                                size=11,
                                color=c["text_secondary"],
                            ),
                        ],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.icons.REMOVE_ROUNDED,
                                icon_size=14,
                                on_click=lambda e, pid=item["id"]: self._update_quantity(pid, -1),
                                icon_color=c["text_secondary"],
                                style=ft.ButtonStyle(padding=ft.padding.all(4)),
                            ),
                            ft.Text(
                                str(item["quantity"]),
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=c["text"],
                                width=20,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            ft.IconButton(
                                ft.icons.ADD_ROUNDED,
                                icon_size=14,
                                on_click=lambda e, pid=item["id"]: self._update_quantity(pid, 1),
                                icon_color=AppTheme.ACCENT,
                                style=ft.ButtonStyle(padding=ft.padding.all(4)),
                            ),
                        ],
                        spacing=0,
                        tight=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                f"${item['subtotal']:,.2f}",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=AppTheme.ACCENT,
                            ),
                            ft.IconButton(
                                ft.icons.CLOSE_ROUNDED,
                                icon_size=14,
                                on_click=lambda e, pid=item["id"]: self._remove_from_cart(pid),
                                icon_color=AppTheme.ERROR,
                                style=ft.ButtonStyle(padding=ft.padding.all(2)),
                            ),
                        ],
                        spacing=0,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=self.colors["surface"] if self.is_dark else self.colors["bg"],
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border=ft.border.all(1, self.colors["border"]),
        )

    # ─── Checkout dialog ──────────────────────────────────────────
    def _show_checkout_dialog(self, e):
        if not self.cart:
            self.app.show_snackbar("El carrito está vacío", error=True)
            return

        c = self.colors
        total = sum(i["subtotal"] for i in self.cart)
        method_ref = ft.Ref[ft.RadioGroup]()
        amount_field = AppTheme.make_text_field(
            "Monto recibido", f"{total:.2f}", colors=c
        )
        change_text = ft.Text("Cambio: $0.00", size=14, color=AppTheme.SUCCESS, weight=ft.FontWeight.W_600)

        def on_amount_change(e):
            try:
                received = float(amount_field.value or 0)
                change = received - total
                change_text.value = f"Cambio: ${max(0, change):,.2f}"
                change_text.color = AppTheme.SUCCESS if change >= 0 else AppTheme.ERROR
            except ValueError:
                change_text.value = "Cambio: $0.00"
            self.page.update()

        amount_field.on_change = on_amount_change

        def on_confirm(e):
            method = method_ref.current.value or "cash"
            try:
                received = float(amount_field.value or 0)
            except ValueError:
                received = total

            dialog.open = False
            self.page.update()

            result = self.sale_controller.create_sale(self.cart, method, received)
            if result:
                self.cart.clear()
                self._refresh_cart()
                self._show_receipt(result, method)

        def on_cancel(e):
            dialog.open = False
            self.page.update()

        method_group = ft.RadioGroup(
            ref=method_ref,
            value="cash",
            content=ft.Row(
                [
                    ft.Radio(value="cash", label="Efectivo"),
                    ft.Radio(value="card", label="Tarjeta"),
                    ft.Radio(value="transfer", label="Transferencia"),
                ],
                spacing=12,
            ),
        )

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                [
                    ft.Icon(ft.icons.PAYMENT_ROUNDED, color=AppTheme.ACCENT),
                    ft.Text("Procesar Pago", weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Total a cobrar", size=13, color=c["text_secondary"]),
                                    ft.Text(
                                        f"${total:,.2f}",
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppTheme.ACCENT,
                                    ),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                            ),
                            alignment=ft.alignment.center,
                            padding=ft.padding.symmetric(vertical=16),
                        ),
                        ft.Text("Método de pago", size=13, color=c["text_secondary"]),
                        method_group,
                        ft.Container(height=8),
                        amount_field,
                        ft.Container(height=8),
                        change_text,
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=340,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=on_cancel),
                ft.Container(
                    content=ft.Text("Confirmar Pago", color="white", weight=ft.FontWeight.W_600),
                    gradient=AppTheme.gradient_primary(),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    on_click=on_confirm,
                    ink=True,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def _show_receipt(self, result: dict, method: str):
        sale = result["sale"]
        total = result["total"]
        change = result.get("change", 0)

        method_labels = {"cash": "Efectivo", "card": "Tarjeta", "transfer": "Transferencia"}
        method_label = method_labels.get(method, method)

        items_col = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(item["name"], size=13, expand=True),
                        ft.Text(f"{item['quantity']}x", size=12, color="#8B8FA8"),
                        ft.Text(f"${item['subtotal']:,.2f}", size=13, weight=ft.FontWeight.W_600),
                    ]
                )
                for item in self.cart
            ]
            or [
                ft.Row(
                    [
                        ft.Text("Venta completada", size=13),
                        ft.Text(f"${total:,.2f}", size=13, weight=ft.FontWeight.W_600),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            ],
            spacing=6,
        )

        def close(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Icon(ft.icons.CHECK_CIRCLE_ROUNDED, color=AppTheme.SUCCESS),
                    ft.Text("Ticket de Venta", weight=ft.FontWeight.BOLD),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        items_col,
                        ft.Divider(),
                        ft.Row(
                            [
                                ft.Text("Método:", size=13),
                                ft.Text(method_label, size=13, weight=ft.FontWeight.W_600),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            [
                                ft.Text("Total:", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f"${total:,.2f}",
                                    size=14,
                                    weight=ft.FontWeight.BOLD,
                                    color=AppTheme.ACCENT,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Row(
                            [
                                ft.Text("Cambio:", size=13),
                                ft.Text(
                                    f"${change:,.2f}",
                                    size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=AppTheme.SUCCESS,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=320,
            ),
            actions=[
                ft.Container(
                    content=ft.Text("Nueva venta", color="white", weight=ft.FontWeight.W_600),
                    gradient=AppTheme.gradient_success(),
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=16, vertical=8),
                    on_click=close,
                    ink=True,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()