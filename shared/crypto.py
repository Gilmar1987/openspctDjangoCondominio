"""Criptografia de campos sensíveis e hash determinístico (ADR-0009).

- encrypt/decrypt: Fernet (AES + HMAC) com settings.FIELD_ENCRYPTION_KEY; não determinístico.
- keyed_hash: HMAC-SHA256 com settings.CPF_HASH_KEY; determinístico, usado em unicidade e busca
  sem decifrar a tabela.
"""

import hashlib
import hmac

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    return Fernet(settings.FIELD_ENCRYPTION_KEY)


def encrypt(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


def keyed_hash(text: str) -> str:
    return hmac.new(settings.CPF_HASH_KEY.encode(), text.encode(), hashlib.sha256).hexdigest()
