from django.db import models

from people.models import PersonModel


class ResidentRecord(PersonModel):
    """Morador: herda de PersonModel os campos e o CPF único por condomínio (ADR-0016).

    A FK com PROTECT impede excluir um apartamento que tenha moradores; a referência por
    string evita importar apartments.models (ADR-0015).
    """

    apartment = models.ForeignKey(
        "apartments.ApartmentRecord",
        on_delete=models.PROTECT,
        db_column="apartment_id",
        related_name="+",
    )

    class Meta(PersonModel.Meta):
        db_table = "resident"
