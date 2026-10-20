"""Tradução dos erros do Pydantic para mensagens em pt-BR (ADR-0014).

O mesmo dicionário {campo: [mensagens]} é usado pela API e pelas páginas HTML,
garantindo mensagens idênticas nas duas interfaces.
"""

from pydantic import ValidationError

NON_FIELD = "__all__"


def _message(error, label):
    kind = error["type"]
    ctx = error.get("ctx") or {}
    if kind == "missing" or (kind == "string_too_short" and ctx.get("min_length") == 1):
        return f"O campo {label} é obrigatório."
    if kind == "string_too_short":
        return f"O campo {label} deve ter no mínimo {ctx['min_length']} caracteres."
    if kind == "string_too_long":
        return f"O campo {label} deve ter no máximo {ctx['max_length']} caracteres."
    if kind == "string_type":
        return f"O campo {label} deve ser um texto."
    if kind in ("int_parsing", "int_type", "int_from_float"):
        return f"O campo {label} deve ser um número inteiro."
    if kind == "value_error":
        return str(ctx["error"])
    return f"O campo {label} é inválido."


def to_ptbr_errors(exc: ValidationError, labels: dict[str, str]) -> dict[str, list[str]]:
    errors: dict[str, list[str]] = {}
    for error in exc.errors():
        field = str(error["loc"][0]) if error["loc"] else NON_FIELD
        errors.setdefault(field, []).append(_message(error, labels.get(field, field)))
    return errors
