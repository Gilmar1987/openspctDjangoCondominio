"""Domínio de condomínios em Python puro (ADR-0014): sem Django, DRF ou Pydantic."""

import uuid
from dataclasses import dataclass, replace
from typing import Optional


class InvalidCondominiumError(ValueError):
    pass


@dataclass(frozen=True)
class Condominium:
    id: Optional[uuid.UUID]
    name: str

    @classmethod
    def create(cls, name: str) -> "Condominium":
        name = name.strip()
        if not name:
            raise InvalidCondominiumError("O nome do condomínio é obrigatório.")
        return cls(id=None, name=name)

    def with_id(self, condominium_id: uuid.UUID) -> "Condominium":
        return replace(self, id=condominium_id)
