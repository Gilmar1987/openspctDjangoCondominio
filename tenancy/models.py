import uuid

from django.db import models


class Condominium(models.Model):
    """Condomínio atendido pelo produto; é o tenant (ADR-0007, ADR-0013)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)

    class Meta:
        db_table = "condominium"

    def __str__(self):
        return self.name


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant_id):
        return self.filter(tenant_id=tenant_id)


class TenantOwnedModel(models.Model):
    """Base de todo model de negócio: coluna tenant_id indexada e consultas via for_tenant()."""

    tenant = models.ForeignKey(
        Condominium,
        on_delete=models.PROTECT,
        db_column="tenant_id",
        related_name="+",
    )

    objects = TenantQuerySet.as_manager()

    class Meta:
        abstract = True
