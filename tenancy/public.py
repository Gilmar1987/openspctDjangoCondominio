"""API pública de tenancy: único ponto que as fatias de negócio importam (ADR-0013)."""

import uuid
from dataclasses import dataclass

from django.http import Http404

from tenancy.models import Condominium, TenantOwnedModel

__all__ = ["Condominium", "TenantOwnedModel", "TenantRef", "get_condominium_or_404"]


@dataclass(frozen=True)
class TenantRef:
    id: uuid.UUID
    name: str


def get_condominium_or_404(condominium_id) -> TenantRef:
    try:
        condominium = Condominium.objects.get(id=condominium_id)
    except Condominium.DoesNotExist:
        raise Http404
    return TenantRef(id=condominium.id, name=condominium.name)
