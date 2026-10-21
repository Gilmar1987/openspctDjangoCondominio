# Verificações — correcoes-de-seguranca

## 2026-10-21

- Críticos: 0
- Warnings: 0
- Sugestões: 1
- Não verificado: —
- Cobertura fora da suíte: —
- Avaliação: No critical issues or warnings. 1 suggestion(s) to consider. Ready for archive (with noted improvements).

Itens:

- [sugestão] README não cita a auditoria de dependências entre os comandos de teste (`README.md`, seção "Testes")

Comandos:

- `gh run view 39649576157` (PR #5, commit 8fe9ebc) → "No known vulnerabilities found", "No changes detected", 357 passed, 100% nos 5 `*/domain.py` (exit 0; reused from apply)
- `gh run list --branch main` → run 39650947487 no merge 48db76d: success (exit 0)
- `git diff --name-only 8fe9ebc HEAD -- . ':!*.md'` → nenhum arquivo de código mudou após o commit verificado (exit 0)
- `docker compose run --rm web pytest tests/shared -rf --durations=3` → 35 passed, pior caso de tempo 0,07 s (exit 0; reused from apply)
- `pip-audit -r requirements.txt --progress-spinner off` → No known vulnerabilities found (exit 0; reused from apply)
