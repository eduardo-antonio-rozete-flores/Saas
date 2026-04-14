# presentation/theme.py

import flet as ft


class AppTheme:
    ACCENT = "#6C63FF"
    ACCENT_HOVER = "#7D75FF"
    SUCCESS = "#00D9A3"
    WARNING = "#FFB347"
    ERROR = "#FF5F7E"
    PINK = "#FF6B9D"
    BLUE = "#00B4D8"

    DARK = {
        "bg": "#0F1117",
        "surface": "#1A1D2E",
        "card": "#252840",
        "border": "#353858",
        "text": "#E8E9F3",
        "text_secondary": "#8B8FA8",
        "sidebar": "#13152A",
        "input_fill": "#1E2139",
        "hover": "#2E3155",
        "divider": "#2A2D48",
    }

    LIGHT = {
        "bg": "#F0F2FF",
        "surface": "#FFFFFF",
        "card": "#FFFFFF",
        "border": "#E4E6F0",
        "text": "#1A1D2E",
        "text_secondary": "#6B7280",
        "sidebar": "#FFFFFF",
        "input_fill": "#F5F6FF",
        "hover": "#F0F2FF",
        "divider": "#E8EAF0",
    }

    # ─── Gradients ────────────────────────────────────────────────
    @staticmethod
    def gradient_primary():
        return ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#6C63FF", "#FF6B9D"],
        )

    @staticmethod
    def gradient_success():
        return ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#00D9A3", "#00B4D8"],
        )

    @staticmethod
    def gradient_warning():
        return ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#FFB347", "#FF6B9D"],
        )

    @staticmethod
    def gradient_error():
        return ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#FF5F7E", "#FF8C6B"],
        )

    @staticmethod
    def gradient_info():
        return ft.LinearGradient(
            begin=ft.alignment.center_left,
            end=ft.alignment.center_right,
            colors=["#00B4D8", "#6C63FF"],
        )

    @staticmethod
    def gradient_auth_panel():
        return ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#6C63FF", "#FF6B9D", "#FFB347"],
            stops=[0.0, 0.6, 1.0],
        )

    # ─── Reusable Components ──────────────────────────────────────
    @staticmethod
    def make_text_field(
        label,
        hint="",
        password=False,
        width=None,
        value="",
        ref=None,
        colors=None,
    ):
        c = colors or AppTheme.DARK
        return ft.TextField(
            label=label,
            hint_text=hint,
            password=password,
            can_reveal_password=password,
            value=value,
            ref=ref,
            border_radius=12,
            border_color=c["border"],
            focused_border_color=AppTheme.ACCENT,
            label_style=ft.TextStyle(color=c["text_secondary"], size=13),
            text_style=ft.TextStyle(color=c["text"]),
            cursor_color=AppTheme.ACCENT,
            bgcolor=c["input_fill"],
            width=width,
            content_padding=ft.padding.symmetric(horizontal=16, vertical=14),
        )

    @staticmethod
    def primary_button(text, on_click=None, width=None, icon=None):
        content = (
            ft.Row(
                [ft.Icon(icon, color="white", size=18), ft.Text(text, color="white", weight=ft.FontWeight.W_600)],
                spacing=8,
                tight=True,
            )
            if icon
            else ft.Text(text, color="white", weight=ft.FontWeight.W_600)
        )
        return ft.Container(
            content=content,
            gradient=AppTheme.gradient_primary(),
            border_radius=12,
            padding=ft.padding.symmetric(horizontal=24, vertical=14),
            width=width,
            alignment=ft.alignment.center,
            on_click=on_click,
            ink=True,
        )

    @staticmethod
    def stat_card(title, value, icon, gradient, colors):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, color="white", size=26),
                        width=52,
                        height=52,
                        border_radius=14,
                        gradient=gradient,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(title, size=12, color=colors["text_secondary"], weight=ft.FontWeight.W_500),
                            ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=colors["text"]),
                        ],
                        spacing=2,
                        tight=True,
                    ),
                ],
                spacing=16,
            ),
            padding=ft.padding.all(20),
            bgcolor=colors["card"],
            border_radius=16,
            border=ft.border.all(1, colors["border"]),
            expand=True,
        )

    @staticmethod
    def page_header(title, subtitle, colors, action=None):
        row_controls = [
            ft.Column(
                [
                    ft.Text(title, size=22, weight=ft.FontWeight.BOLD, color=colors["text"]),
                    ft.Text(subtitle, size=13, color=colors["text_secondary"]),
                ],
                spacing=2,
                tight=True,
                expand=True,
            )
        ]
        if action:
            row_controls.append(action)
        return ft.Row(row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)