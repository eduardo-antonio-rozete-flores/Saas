# application/use_cases/register_user_use_case.py
#
# Caso de uso: Registro de nuevo usuario + creación de tenant.
#
# ANTES (en AuthService.register):
#   • Validaciones mezcladas con la orquestación multi-paso
#   • Excepciones genéricas (Exception/ValueError)
#   • Sin distinción entre fallo de auth vs fallo de tenant vs fallo de perfil
#
# AHORA:
#   • Recibe RegisterRequest — validado en el use case
#   • Lanza excepciones específicas (AuthenticationError, RepositoryError)
#   • AuthService mantiene login() y logout() (responsabilidades distintas)
#   • La secuencia queda documentada como pasos explícitos y numerados

import uuid
from domain.schemas.auth_schemas import RegisterRequest
from domain.exceptions import AuthenticationError, RepositoryError


class RegisterUserUseCase:

    def __init__(self, auth_repo, tenant_repo):
        """
        Args:
            auth_repo:   AuthRepository   (requerido)
            tenant_repo: TenantRepository (requerido)
        """
        self.auth_repo   = auth_repo
        self.tenant_repo = tenant_repo

    def execute(self, request: RegisterRequest):
        """
        Registra un nuevo usuario y crea su espacio de trabajo.

        Args:
            request: RegisterRequest (sin validar aún).

        Returns:
            El objeto user de Supabase Auth.

        Raises:
            ValidationError:     datos de entrada inválidos.
            AuthenticationError: Supabase no pudo crear el usuario.
            RepositoryError:     fallo al crear tenant o perfil.
        """
        # 1. Validar DTO (lanza ValidationError si algo falla)
        request.validate()

        # 2. Crear usuario en Supabase Auth
        res  = self.auth_repo.sign_up(request.email, request.password)
        user = res.user
        if not user:
            raise AuthenticationError(
                "No se pudo crear el usuario. Verifica que el email no esté registrado."
            )

        # 3. Crear tenant (workspace del negocio)
        tenant_id  = str(uuid.uuid4())
        tenant_name = f"Negocio de {request.email.split('@')[0]}"
        tenant_res  = self.tenant_repo.create({"id": tenant_id, "name": tenant_name})
        if not tenant_res.data:
            raise RepositoryError(
                "No se pudo crear el espacio de trabajo. Contacta al soporte."
            )

        # 4. Crear perfil (link usuario ↔ tenant + rol admin)
        profile_res = self.auth_repo.create_profile(user.id, tenant_id, role="admin")
        if not profile_res.data:
            raise RepositoryError(
                "No se pudo crear el perfil de usuario. Contacta al soporte."
            )

        return user
