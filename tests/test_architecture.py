"""Fronteiras entre apps (ADR-0015, ADR-0016).

Um app de negócio só importa de outro app o seu `public.py`; de `tenancy`, só `tenancy.public`;
de `people`, só as bases `people.domain`, `people.models` e `people.inputs`; `shared` é livre.
`people` é plataforma e não importa apps de negócio.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUSINESS_APPS = ("condominiums", "apartments", "owners", "residents")
PLATFORM_ALLOWED = {
    "tenancy": {"tenancy.public"},
    "people": {"people.domain", "people.models", "people.inputs"},
}


def imported_modules(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module
            for alias in node.names:
                yield f"{node.module}.{alias.name}"


def violations(app: str):
    found = []
    for path in (ROOT / app).rglob("*.py"):
        if "migrations" in path.parts:
            continue
        for module in imported_modules(path):
            top = module.split(".")[0]
            if top == app or top == "shared":
                continue
            if top in BUSINESS_APPS:
                if app == "people" or module not in (top, f"{top}.public") and not module.startswith(f"{top}.public."):
                    found.append(f"{path.relative_to(ROOT)}: {module}")
            elif top in PLATFORM_ALLOWED:
                allowed = PLATFORM_ALLOWED[top]
                if module != top and not any(module == a or module.startswith(f"{a}.") for a in allowed):
                    found.append(f"{path.relative_to(ROOT)}: {module}")
    return found


@pytest.mark.parametrize("app", [*BUSINESS_APPS, "people"])
def test_app_respects_boundaries(app):
    if not (ROOT / app).exists():
        pytest.skip(f"{app} ainda não existe")

    assert violations(app) == []
