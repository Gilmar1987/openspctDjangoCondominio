import logging

import pytest

from shared.logging import PersonalDataFilter


def handlers_reached(name):
    logger = logging.getLogger(name)
    while logger:
        # Ignora os handlers de captura que o próprio pytest instala no logger raiz.
        yield from (h for h in logger.handlers if not type(h).__module__.startswith("_pytest"))
        logger = logger.parent if logger.propagate else None


@pytest.mark.parametrize("name", ["", "django", "django.request", "django.server", "owners", "apartments"])
def test_every_handler_masks_personal_data(name):
    handlers = list(handlers_reached(name))

    assert handlers
    assert all(any(isinstance(f, PersonalDataFilter) for f in h.filters) for h in handlers)
