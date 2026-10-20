from condominiums.domain import Condominium


def as_json(condominium: Condominium) -> dict:
    return {"id": str(condominium.id), "name": condominium.name}
