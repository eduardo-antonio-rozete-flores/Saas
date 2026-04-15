# presentation/views/ticket_history_view.py
#
# NUEVA VISTA — Fase 3 (Tickets).
#
# RESPONSABILIDAD:
#   Mostrar el historial de tickets del tenant con opción de reimprimir PDF.
#   NO contiene lógica de negocio: sólo delega en ticket_service.
#
# PATRÓN:
#   Recibe ticket_service inyectado. Sigue el mismo patrón que todas las
#   vistas del proyecto: build() retorna el control raíz.
#
# LAYOUT:
#   ┌──────────────────────────────────────────────────┐
#   │ 🧾  Historial de Tickets          [🔄 Actualizar] │
#   ├──────┬──────────┬────────┬───────────┬───────────┤
#   │Folio │  Fecha   │ Total  │   Método  │  Acción   │
#   ├──────┼──────────┼────────┼───────────┼───────────┤
#   │  …   │    …     │   …    │     …     │ [PDF]     │
#   └──────┴──────────┴────────┴───────────┴───────────┘

import os
import subprocess
import sys

import flet as ft

_PRIMARY   = "#6C63FF"
_CARD_BG   = "#FFFFFF"
_BG        = "#F5F6FA"
_TEXT_DARK = "#2D3142"
_TEXT_GRAY = "#9094A6"

_METHOD_LABELS = {
    "cash":     "Efectivo",
    "card":     "Tarjeta",
    "transfer": "Transferencia",
}


class TicketHistoryView:

    def __init__(self, ticket_service, page: ft.Page):
        """
        Args:
            ticket_service: TicketService — inyectado desde el router.
            page:           ft.Page       — para snackbars y updates.
        """
        self.service = ticket_service
        self.page    = page

        self._table_ref   = ft.Ref[ft.DataTable]()
        self._loading_ref = ft.Ref[ft.ProgressRing]()
        self._empty_ref   = ft.Ref[ft.Text]()

    # ──────────────────────────────────────────────────────────
    # Build
    # ──────────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        return ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=20,
            controls=[
                self._header(),
                ft.ProgressRing(ref=self._loading_ref, visible=True),
                ft.Text(
                    ref=self._empty_ref,
                    value="No hay tickets registrados aún.",
                    color=_TEXT_GRAY,
                    visible=False,
                ),
                ft.Container(
                    bgcolor=_CARD_BG,
                    border_radius=12,
                    padding=ft.padding.all(16),
                    shadow=ft.BoxShadow(
                        blur_radius=8,
                        color=ft.colors.with_opacity(0.08, "#000000"),
                    ),
                    content=ft.DataTable(
                        ref=self._table_ref,
                        visible=False,
                        border_radius=8,
                        heading_row_color=ft.colors.with_opacity(0.04, _PRIMARY),
                        data_row_min_height=48,
                        columns=[
                            ft.DataColumn(ft.Text("Folio",  weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Fecha",  weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Total",  weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Método", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("PDF",    weight=ft.FontWeight.BOLD)),
                        ],
                        rows=[],
                    ),
                ),
            ],
        )

    # ──────────────────────────────────────────────────────────
    # Carga de datos (ejecutar en hilo separado)
    # ──────────────────────────────────────────────────────────
    def load(self):
        try:
            tickets = self.service.get_history()
        except Exception as e:
            self._loading_ref.current.visible = False
            self._show_snack(f"Error: {e}", error=True)
            self.page.update()
            return

        self._loading_ref.current.visible = False

        if not tickets:
            self._empty_ref.current.visible = True
            self.page.update()
            return

        self._table_ref.current.rows    = [self._build_row(t) for t in tickets]
        self._table_ref.current.visible = True
        self.page.update()

    # ──────────────────────────────────────────────────────────
    # Construir fila de la tabla
    # ──────────────────────────────────────────────────────────
    def _build_row(self, ticket: dict) -> ft.DataRow:
        folio   = ticket.get("folio", "—")
        fecha   = str(ticket.get("generated_at", ""))[:19].replace("T", " ")
        total   = f"${float(ticket.get('total', 0)):,.2f}"
        method  = _METHOD_LABELS.get(ticket.get("payment_method", ""), ticket.get("payment_method", ""))

        return ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(folio, weight=ft.FontWeight.W_500, color=_PRIMARY)),
                ft.DataCell(ft.Text(fecha, color=_TEXT_GRAY, size=12)),
                ft.DataCell(ft.Text(total, weight=ft.FontWeight.BOLD, color=_TEXT_DARK)),
                ft.DataCell(ft.Text(method, color=_TEXT_GRAY)),
                ft.DataCell(
                    ft.IconButton(
                        icon=ft.icons.PICTURE_AS_PDF_ROUNDED,
                        tooltip="Generar / abrir PDF",
                        icon_color=_PRIMARY,
                        on_click=lambda _, t=ticket: self._on_print(t),
                    )
                ),
            ]
        )

    # ──────────────────────────────────────────────────────────
    # Acción: reimprimir / abrir PDF
    # ──────────────────────────────────────────────────────────
    def _on_print(self, ticket: dict):
        """
        Regenera el PDF del ticket y lo abre con el visor del sistema.
        Reconstruye el dict completo desde el campo 'payload' guardado en DB.
        """
        try:
            full_ticket = ticket.get("payload") or ticket
            path = self.service.export_pdf(full_ticket)
            self._open_file(path)
            self._show_snack(f"PDF abierto: {path}")
        except Exception as e:
            self._show_snack(f"Error generando PDF: {e}", error=True)

    @staticmethod
    def _open_file(path: str):
        """Abre el PDF con el visor predeterminado del SO."""
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    # ──────────────────────────────────────────────────────────
    # Header
    # ──────────────────────────────────────────────────────────
    def _header(self) -> ft.Control:
        return ft.Row(
            controls=[
                ft.Icon(ft.icons.RECEIPT_LONG_ROUNDED, color=_PRIMARY, size=28),
                ft.Text(
                    "Historial de Tickets",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=_TEXT_DARK,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.REFRESH_ROUNDED,
                    tooltip="Actualizar",
                    on_click=lambda _: self.page.run_thread(self.load),
                ),
            ]
        )

    # ──────────────────────────────────────────────────────────
    # Snackbar helper
    # ──────────────────────────────────────────────────────────
    def _show_snack(self, msg: str, error: bool = False):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=ft.colors.RED_400 if error else ft.colors.GREEN_400,
            open=True,
        )
        self.page.update()