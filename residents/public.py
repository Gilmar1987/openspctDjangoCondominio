"""Contrato público de moradores (ADR-0015): único módulo que outros apps importam.

Expõe só contagens e identificadores; nunca dados pessoais (ADR-0017).
"""

import uuid

from residents import repository

__all__ = ["count_by_apartment", "count_in_apartment", "residences_by_cpf_hash"]


def count_by_apartment(tenant_id) -> dict[uuid.UUID, int]:
    return repository.count_by_apartment(tenant_id)


def count_in_apartment(tenant_id, apartment_id) -> int:
    return repository.count_in_apartment(tenant_id, apartment_id)


def residences_by_cpf_hash(tenant_id, hashes) -> dict[str, uuid.UUID]:
    """hash do CPF -> apartamento onde a pessoa mora, no mesmo condomínio (ADR-0017)."""
    hashes = list(hashes)
    return repository.residences_by_cpf_hash(tenant_id, hashes) if hashes else {}
