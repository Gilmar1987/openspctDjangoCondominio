import uuid

from django.db import models
from django.db.models import F, Value
from django.db.models.functions import Coalesce, Lower

from tenancy.public import TenantOwnedModel

UNIQUE_CONSTRAINT = "uniq_apartment_per_tenant"


def key_expressions():
    """Torre + bloco + número sem diferenciar maiúsculas, com ausentes iguais (D5)."""
    return {
        "key_tower": Lower(Coalesce("tower", Value(""))),
        "key_block": Lower(Coalesce("block", Value(""))),
        "key_number": Lower("number"),
    }


class ApartmentRecord(TenantOwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tower = models.CharField(max_length=20, null=True, blank=True)
    block = models.CharField(max_length=20, null=True, blank=True)
    floor = models.SmallIntegerField(null=True, blank=True)
    number = models.CharField(max_length=10)

    class Meta:
        db_table = "apartment"
        constraints = [
            models.UniqueConstraint(
                F("tenant"),
                *key_expressions().values(),
                name=UNIQUE_CONSTRAINT,
            ),
        ]
