from people.models import PersonModel


class OwnerRecord(PersonModel):
    """Proprietário: herda de PersonModel todos os campos (ADR-0016).

    O vínculo com apartamentos é a FK `owner_id` do lado de `apartment`.
    """

    class Meta(PersonModel.Meta):
        db_table = "owner"
