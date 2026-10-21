import logging
import uuid

import pytest

from shared.logging import PersonalDataFilter, redact


@pytest.mark.parametrize(
    "text, leaked",
    [
        ("cpf 529.982.247-25 recusado", "529.982.247-25"),
        ("cpf 52998224725 recusado", "52998224725"),
        ("contato maria@exemplo.com", "maria@exemplo.com"),
        ("fone (81) 99999-0000", "99999-0000"),
        ("fone 81999990000", "81999990000"),
        ("fone 8133334444", "8133334444"),
    ],
)
def test_redact_masks_personal_data(text, leaked):
    assert leaked not in redact(text)


def test_redact_keeps_uuids_and_plain_text():
    identifier = str(uuid.UUID("12345678-1234-1234-1234-123456789012"))
    text = f"owner rejected tenant={identifier} fields=['cpf']"

    assert redact(text) == text


def make_record(msg, args=()):
    return logging.LogRecord("t", logging.INFO, __file__, 1, msg, args, None)


def test_filter_masks_message_and_tuple_args():
    record = make_record("cpf %s e-mail %s qtd %d", ("52998224725", "a@b.com", 3))

    assert PersonalDataFilter().filter(record) is True
    message = record.getMessage()
    assert "52998224725" not in message and "a@b.com" not in message
    assert message.endswith("qtd 3")


def test_filter_masks_dict_args():
    record = make_record("cpf %(cpf)s", ({"cpf": "529.982.247-25"},))

    PersonalDataFilter().filter(record)

    assert "529.982.247-25" not in record.getMessage()


def test_filter_handles_non_string_message():
    record = make_record(ValueError("cpf 52998224725"))

    PersonalDataFilter().filter(record)

    assert "52998224725" not in record.getMessage()


# Desempenho: o filtro roda em todo log, então precisa ser linear (change correcoes-de-seguranca).

import time

WORST_CASES = {
    "sem-arroba": "a." * 50_000,
    "arroba-no-fim": "a." * 50_000 + "@",
    "so-digitos": "1" * 100_000,
    "telefones": "(81) " * 20_000,
}


@pytest.mark.parametrize("text", WORST_CASES.values(), ids=WORST_CASES.keys())
def test_redact_is_linear_on_worst_cases(text):
    start = time.perf_counter()
    redact(text)

    assert time.perf_counter() - start < 0.5


def test_email_with_64_char_local_part_is_masked():
    email = "a" * 64 + "@exemplo.com"

    assert email not in redact(f"contato {email}")


def test_long_domain_label_does_not_hang():
    text = "x@" + "d" * 70 + ".com"
    start = time.perf_counter()
    redact(text)

    assert time.perf_counter() - start < 0.5
