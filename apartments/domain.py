"""Domínio de apartamentos em Python puro (ADR-0014): sem Django, DRF ou Pydantic."""

import uuid
from dataclasses import dataclass, replace
from typing import Iterable, Optional

DUPLICATE_MESSAGE = "Este apartamento já existe neste condomínio."


class InvalidApartmentError(ValueError):
    pass


class DuplicateApartmentError(Exception):
    def __init__(self):
        super().__init__(DUPLICATE_MESSAGE)


def normalize_text(value: Optional[str]) -> Optional[str]:
    """Remove espaços nas extremidades; texto em branco vira ausente (None)."""
    if value is None:
        return None
    return value.strip() or None


def _required_number(number: Optional[str]) -> str:
    number = normalize_text(number)
    if number is None:
        raise InvalidApartmentError("O número do apartamento é obrigatório.")
    return number


@dataclass(frozen=True)
class Apartment:
    id: Optional[uuid.UUID]
    tenant_id: uuid.UUID
    tower: Optional[str]
    block: Optional[str]
    floor: Optional[int]
    number: str
    owner_id: Optional[uuid.UUID] = None

    @classmethod
    def create(cls, tenant_id, number, tower=None, block=None, floor=None, owner_id=None) -> "Apartment":
        return cls(
            id=None,
            tenant_id=tenant_id,
            tower=normalize_text(tower),
            block=normalize_text(block),
            floor=floor,
            number=_required_number(number),
            owner_id=owner_id,
        )

    def update(self, *, number, tower, block, floor, owner_id=None) -> "Apartment":
        """Altera os dados da unidade e o proprietário; id e condomínio nunca mudam."""
        return replace(
            self,
            tower=normalize_text(tower),
            block=normalize_text(block),
            floor=floor,
            number=_required_number(number),
            owner_id=owner_id,
        )

    def with_id(self, apartment_id: uuid.UUID) -> "Apartment":
        return replace(self, id=apartment_id)

    @property
    def natural_key(self) -> tuple[str, str, str]:
        """Torre + bloco + número, sem diferenciar maiúsculas; ausentes contam como iguais."""
        return (
            (self.tower or "").casefold(),
            (self.block or "").casefold(),
            self.number.casefold(),
        )


def ensure_unique(candidate: Apartment, existing: Iterable[Apartment]) -> None:
    for other in existing:
        if other.id != candidate.id and other.natural_key == candidate.natural_key:
            raise DuplicateApartmentError()
