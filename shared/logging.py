"""Filtro que mascara dados pessoais nos logs (ADR-0009).

Rede de segurança para CPF, e-mail e telefone. Nomes de pessoas não são detectáveis por
padrão: por isso as fatias registram só identificadores e nomes de campo, nunca valores.
"""

import logging
import re

_BOUNDARY_START = r"(?<![\w.-])"
_BOUNDARY_END = r"(?![\w-])"

# Todos os quantificadores são limitados para o filtro ser linear no tamanho da mensagem:
# ele roda em todo log, inclusive com URLs enviadas por quem acessa a aplicação.
# E-mail: parte local até 64 e rótulos de domínio até 63 caracteres (RFC 5321).
_EMAIL = re.compile(r"[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,8}")

_PATTERNS = (
    (re.compile(_BOUNDARY_START + r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}" + _BOUNDARY_END), "***.***.***-**"),
    (re.compile(r"\(\d{2}\)\s?\d{4,5}-?\d{4}" + _BOUNDARY_END), "(**) *****-****"),
    (re.compile(_BOUNDARY_START + r"\d{10,11}" + _BOUNDARY_END), "***********"),
)


def redact(text: str) -> str:
    if "@" in text:
        text = _EMAIL.sub("***@***", text)
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _redact_value(value):
    return redact(value) if isinstance(value, str) else value


class PersonalDataFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        if isinstance(record.args, dict):
            record.args = {key: _redact_value(value) for key, value in record.args.items()}
        elif record.args:
            record.args = tuple(_redact_value(value) for value in record.args)
        return True
