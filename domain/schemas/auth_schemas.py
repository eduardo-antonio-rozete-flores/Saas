# domain/schemas/auth_schemas.py
#
# DTOs para operaciones de autenticación.
#
# PROPÓSITO:
#   Centralizar la validación de datos de entrada en objetos explícitos.
#   Los servicios reciben DTOs ya construidos en vez de parámetros sueltos.
#   Esto permite:
#     • Testear la validación sin instanciar servicios ni DB.
#     • Saber exactamente qué campo falló (ValidationError.field).
#     • Reutilizar la misma validación desde cualquier controlador.

from dataclasses import dataclass
from domain.exceptions import ValidationError


@dataclass
class LoginRequest:
    """DTO de entrada para iniciar sesión."""
    email:    str
    password: str

    def validate(self) -> None:
        if not self.email or not self.email.strip():
            raise ValidationError("email", "El email es requerido")
        if "@" not in self.email:
            raise ValidationError("email", "El email no tiene un formato válido")
        if not self.password:
            raise ValidationError("password", "La contraseña es requerida")


@dataclass
class RegisterRequest:
    """DTO de entrada para registrar un nuevo usuario."""
    email:    str
    password: str

    def validate(self) -> None:
        if not self.email or not self.email.strip():
            raise ValidationError("email", "El email es requerido")
        parts = self.email.split("@")
        if len(parts) != 2 or not parts[1] or "." not in parts[1]:
            raise ValidationError("email", "El email no tiene un formato válido")
        if not self.password:
            raise ValidationError("password", "La contraseña es requerida")
        if len(self.password) < 6:
            raise ValidationError("password",
                "La contraseña debe tener al menos 6 caracteres")
