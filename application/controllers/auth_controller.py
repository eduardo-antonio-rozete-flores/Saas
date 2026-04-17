# application/controllers/auth_controller.py
#
# CAMBIOS (refactor arquitectural):
#   • register() usa RegisterUserUseCase cuando está inyectado (preferido).
#     Fallback a AuthService.register() si el use case no está disponible.
#   • Maneja excepciones de dominio específicas en vez de Exception genérica:
#       ValidationError     → campo inválido, mensaje directo al usuario
#       AuthenticationError → credenciales/token, mensaje directo
#       NexaPOSError        → cualquier error de dominio no previsto
#       Exception           → error inesperado del sistema

from domain.exceptions import ValidationError, AuthenticationError, NexaPOSError
from domain.schemas.auth_schemas import RegisterRequest


class AuthController:

    def __init__(self, service, app, register_use_case=None):
        self.service            = service
        self.app                = app
        self._register_use_case = register_use_case

    def login(self, email: str, password: str) -> bool:
        try:
            self.service.login(email, password)
            self.app.navigate_to("dashboard")
            return True
        except (ValidationError, AuthenticationError) as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False
        except Exception as ex:
            self.app.show_snackbar(f"Error al iniciar sesión: {ex}", error=True)
            return False

    def register(self, email: str, password: str) -> bool:
        try:
            if self._register_use_case:
                request = RegisterRequest(email=email, password=password)
                self._register_use_case.execute(request)
            else:
                self.service.register(email, password)

            self.app.show_snackbar(
                "Registro exitoso. Verifica tu email y luego inicia sesión."
            )
            self.app.navigate_to("login")
            return True
        except (ValidationError, NexaPOSError) as ex:
            self.app.show_snackbar(str(ex), error=True)
            return False
        except Exception as ex:
            self.app.show_snackbar(f"Error inesperado: {ex}", error=True)
            return False

    def logout(self):
        self.service.logout()
        self.app.navigate_to("login")
