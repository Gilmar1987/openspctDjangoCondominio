# Design

## Context

A motivação e as medições estão em proposal.md (Why). Hoje o código está assim:
- `shared/logging.py` tem quatro padrões em `_PATTERNS`:
  - **E-mail:** `[\w.+-]+@[\w-]+(?:\.[\w-]+)+`, sem limite de tamanho. Sem `@` na mensagem, o motor tenta cada posição inicial e percorre até o fim, o que é O(n²).
  - **CPF:** `\d{3}\.?\d{3}\.?\d{3}-?\d{2}`, de tamanho fixo.
  - **Telefone com máscara:** `\(\d{2}\)\s?\d{4,5}-?\d{4}`, de tamanho limitado.
  - **10 ou 11 dígitos:** `\d{10,11}`, de tamanho limitado.

  Os três últimos já são lineares. `PersonalDataFilter` aplica `redact` em `record.msg` e em cada argumento de texto, e todo handler de log passa por ele (`tests/shared/test_logging_config.py`).
- `requirements.txt` fixa `djangorestframework==3.16.1` e `pytest==8.4.2`. O DRF está configurado só com `JSONRenderer` e `JSONParser`, sem autenticação (`config/settings.py`).
- O `.github/workflows/ci.yml` tem os passos: instalar, `makemigrations --check` e `pytest --cov`.

## Architecture Decisions

- **ADR-0018** (`openspec/adrs/0018-auditoria-de-dependencias-no-ci.md`, **Proposed**): auditoria de dependências bloqueante no CI. Ela acrescenta uma checagem à decisão 5.3 do `project-setup.md`. Precisa ser promovida a `Accepted` antes do arquivamento (tarefa 4.1).
- Aplicada sem alteração: ADR-0009 (o mascaramento nos logs continua com as mesmas categorias).

## Goals / Non-Goals

**Goals:**
- `redact` em tempo linear com o tamanho do texto, nos piores casos.
- Nenhuma vulnerabilidade conhecida nas dependências fixadas, e o CI falhando quando surgir uma.

**Non-Goals:**
- Mudar as categorias mascaradas ou o formato das máscaras.
- Rate limiting, varredura de secrets e separação de dependências de desenvolvimento (proposal: Fora do escopo).

## Decisions

### D1. Padrão de e-mail limitado e condicionado a `@`
O padrão passa a `[\w.+-]{1,64}@[\w-]{1,63}(?:\.[\w-]{1,63}){1,8}`. Os limites seguem a RFC 5321 (parte local até 64 caracteres; cada rótulo do domínio até 63) e aceitam até 8 subdomínios. `redact` só aplica esse padrão quando `"@" in text`. Assim, o caso comum (log sem e-mail) nem roda o regex, e o pior caso com `@` fica limitado a cerca de 64 tentativas por posição.
*Alternativas:*
- Módulo `regex` com timeout: dependência nova e solução indireta.
- Remover o mascaramento de e-mail: contraria a ADR-0009.

### D2. Demais padrões
Os três outros padrões já têm tamanho fixo ou limitado e ficam como estão. Os testes de tempo (D3) cobrem os quatro, para evitar regressão.

### D3. Testes de tempo
Em `tests/shared/test_logging.py`, cada pior caso tem 100.000 caracteres e precisa terminar em menos de 0,5 s:
- `"a." * 50_000` (sem `@`);
- `"a." * 50_000 + "@"`;
- `"1" * 100_000`;
- `"(81) " * 20_000`.

Usa `time.perf_counter`, com folga para o CI. Os testes de mascaramento atuais continuam, mais casos de limite: e-mail com parte local de 64 caracteres é mascarado, e um rótulo de domínio com mais de 63 caracteres não trava.

### D4. Versões
`djangorestframework==3.17.2` (exige Django ≥ 4.2) e `pytest==9.0.3` (Python ≥ 3.10). São as versões mínimas que corrigem as vulnerabilidades apontadas, compatíveis com Django 5.2, Python 3.12 e `pytest-django==4.14.0` (que aceita pytest ≥ 7), conforme os metadados do PyPI. Se a suíte quebrar com o pytest 9, o ajuste fica nos testes, sem mudar o código da aplicação.

### D5. Passo do CI
Depois de "Instalar dependências", entram:
```yaml
- name: Auditoria de dependências
  run: |
    pip install pip-audit==2.10.1
    pip-audit -r requirements.txt --progress-spinner off
```
Sem `--ignore-vuln` no começo. Eventuais exceções seguem a ADR-0018.

### D6. `project.md` (store)
A linha "Auditoria de dependências" de "Comandos de verificação" passa a ser `pip-audit -r requirements.txt` (com `pip install pip-audit==2.10.1`), com a observação "bloqueante no CI (ADR-0018)".

## Risks / Trade-offs

- **[Regressão no mascaramento de logs (dados pessoais)]** → Todos os testes atuais de `redact` e `PersonalDataFilter` continuam, mais os de limite (D3). `test_logging_config.py` continua garantindo o filtro em todos os handlers.
- **[pytest 9 é versão maior]** → Rodar a suíte completa. Se algum teste quebrar, ajustar o teste e registrar o motivo na tarefa.
- **[Falso positivo ou indisponibilidade do `pip-audit` no CI]** → Versão fixada, exceção documentada conforme a ADR-0018, e rodar o job de novo em caso de falha de rede.
- **[Teste de tempo instável no CI]** → Limite de 0,5 s, cerca de 100 vezes acima do tempo esperado para o padrão linear.

**Raio de impacto**
- Arquivos-alvo: `shared/logging.py`, `tests/shared/test_logging.py`, `requirements.txt`, `.github/workflows/ci.yml`, `openspec/project.md` (store) e `openspec/adrs/0018-...md` (store).
- Dependentes afetados: todo o logging da aplicação (passa pelo filtro) e toda a suíte (versão do pytest).

## Migration Plan

`docker compose up -d --build` reinstala as dependências. Rollback: reverter o commit. Não há dados envolvidos.
