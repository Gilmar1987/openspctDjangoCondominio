"""Base de pessoa em Python puro (ADR-0014, ADR-0016).

`Person` concentra os atributos gerais (nome, CPF, e-mail, telefone) e as regras deles.
Entidades de pessoa (proprietário, futuramente morador) herdam desta classe e acrescentam
só os próprios atributos e regras.
"""

import uuid
from dataclasses import dataclass, replace
from typing import ClassVar, Optional

CPF_LENGTH = 11
PHONE_LENGTHS = (10, 11)


class InvalidPersonError(ValueError):
    pass


class DuplicateCpfError(Exception):
    def __init__(self, role_label: str):
        super().__init__(f"Já existe {role_label} com este CPF neste condomínio.")


def only_digits(value: Optional[str]) -> str:
    return "".join(char for char in value if char.isdigit()) if value else ""


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return value.strip() or None


def _check_digit(digits: str) -> int:
    weight = len(digits) + 1
    total = sum(int(digit) * (weight - index) for index, digit in enumerate(digits))
    remainder = total * 10 % 11
    return 0 if remainder == 10 else remainder


def is_valid_cpf(cpf: str) -> bool:
    """CPF com 11 dígitos, dígitos verificadores corretos e não composto de um só dígito."""
    if len(cpf) != CPF_LENGTH or not cpf.isdigit() or len(set(cpf)) == 1:
        return False
    return _check_digit(cpf[:9]) == int(cpf[9]) and _check_digit(cpf[:10]) == int(cpf[10])


def mask_cpf(cpf: str) -> str:
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**"


def format_phone(phone: Optional[str]) -> Optional[str]:
    if phone is None:
        return None
    return f"({phone[:2]}) {phone[2:-4]}-{phone[-4:]}"


def _general_attributes(name, cpf, email, phone) -> dict:
    name = normalize_text(name)
    if name is None:
        raise InvalidPersonError("O nome é obrigatório.")
    cpf = only_digits(cpf)
    if not is_valid_cpf(cpf):
        raise InvalidPersonError("O CPF é inválido.")
    phone = only_digits(phone) or None
    if phone is not None and len(phone) not in PHONE_LENGTHS:
        raise InvalidPersonError("O telefone é inválido.")
    return {"name": name, "cpf": cpf, "email": normalize_text(email), "phone": phone}


@dataclass(frozen=True)
class Person:
    id: Optional[uuid.UUID]
    tenant_id: uuid.UUID
    name: str
    cpf: str
    email: Optional[str]
    phone: Optional[str]

    ROLE_LABEL: ClassVar[str] = "pessoa"

    @classmethod
    def create(cls, tenant_id, name, cpf, email=None, phone=None, **own):
        """`own` traz os atributos próprios da subclasse (ex.: apartment_id do morador)."""
        return cls(id=None, tenant_id=tenant_id, **_general_attributes(name, cpf, email, phone), **own)

    def update(self, *, name, cpf, email, phone, **own):
        """Altera os atributos gerais e os próprios da subclasse; id e condomínio nunca mudam."""
        return replace(self, **_general_attributes(name, cpf, email, phone), **own)

    def with_id(self, person_id: uuid.UUID):
        return replace(self, id=person_id)

    @property
    def masked_cpf(self) -> str:
        return mask_cpf(self.cpf)
