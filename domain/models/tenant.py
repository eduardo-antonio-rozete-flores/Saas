# domain/models/tenant.py
#
# Entidad de dominio: Tenant (negocio/workspace).

from dataclasses import dataclass


@dataclass
class Tenant:
    """Representa un negocio registrado en NexaPOS."""
    id:   str
    name: str

    @classmethod
    def from_dict(cls, data: dict) -> "Tenant":
        return cls(id=data["id"], name=data["name"])
