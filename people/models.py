"""Model base de pessoa (ADR-0016): abstrato, cada entidade concreta tem a sua tabela.

Concentra os atributos gerais e a proteção do CPF (ADR-0009): o valor é guardado cifrado
(Fernet) e a unicidade por condomínio usa um hash HMAC determinístico.
"""

import uuid

from django.db import models
from django.db.models import F

from shared.crypto import decrypt, encrypt, keyed_hash
from tenancy.public import TenantOwnedModel

CPF_CONSTRAINT_SUFFIX = "uniq_cpf_per_tenant"


class PersonModel(TenantOwnedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    cpf_encrypted = models.TextField()
    cpf_hash = models.CharField(max_length=64)
    email = models.CharField(max_length=254, null=True, blank=True)
    phone = models.CharField(max_length=11, null=True, blank=True)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                F("tenant"),
                "cpf_hash",
                name=f"%(app_label)s_%(class)s_{CPF_CONSTRAINT_SUFFIX}",
            ),
        ]

    @classmethod
    def cpf_constraint_name(cls) -> str:
        return f"{cls._meta.app_label}_{cls.__name__.lower()}_{CPF_CONSTRAINT_SUFFIX}"

    @staticmethod
    def hash_cpf(cpf_digits: str) -> str:
        return keyed_hash(cpf_digits)

    def set_cpf(self, cpf_digits: str) -> None:
        self.cpf_encrypted = encrypt(cpf_digits)
        self.cpf_hash = self.hash_cpf(cpf_digits)

    def get_cpf(self) -> str:
        return decrypt(self.cpf_encrypted)
