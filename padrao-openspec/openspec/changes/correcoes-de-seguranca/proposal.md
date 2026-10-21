# Proposal

## Why

Uma revisão de segurança externa do código, verificada nesta sessão contra o código e com testes práticos, confirmou três problemas:

1. **O filtro de dados pessoais dos logs fica quadrático.** O padrão de e-mail em `shared/logging.py` leva 0,04 s com 2.000 caracteres sem `@`, 5,7 s com 20.000 e 177 s com 100.000. O filtro roda em todo log, inclusive no "Not Found: /caminho" do Django, então uma URL longa e maliciosa pode prender a thread do servidor.
2. **Há dependências com vulnerabilidades conhecidas.** O `pip-audit` aponta `djangorestframework 3.16.1` (PYSEC-2026-3827 e PYSEC-2026-3828, corrigidas na 3.17.2) e `pytest 8.4.2` (PYSEC-2026-1845, corrigida na 9.0.3).
3. **Nada no fluxo detecta isso.** O `project.md` diz "Auditoria de dependências: Não aplicável no MVP", e o CI roda só os testes (decisão 5.3). As vulnerabilidades só apareceram numa revisão manual.

A mesma revisão apontou CSRF e XSS como "High", mas os dois foram descartados: o CSRF do Django está ativo nas páginas, e a API só aceita JSON, sem CORS. Não há saída sem escape. Ela também apontou a falta de rate limiting, que é uma decisão registrada (decisão 6.4 "Nenhuma no MVP", aplicação só local), e não um defeito.

**Resultado esperado:** o filtro de logs roda em tempo linear com o tamanho da mensagem, as dependências não têm vulnerabilidade conhecida, e o CI falha quando uma dependência passar a ter.

## What Changes

- **Filtro de logs em tempo linear:**
  - os padrões de `shared/logging.py` passam a ter quantificadores limitados;
  - o padrão de e-mail só roda em textos que contêm `@`;
  - a regra de mascaramento de CPF, e-mail e telefone continua a mesma.
- **Dependências atualizadas:** `djangorestframework==3.17.2` e `pytest==9.0.3` no `requirements.txt`. As versões são as primeiras que corrigem as vulnerabilidades apontadas.
- **Auditoria de dependências no CI:** um passo `pip-audit` no `ci.yml` faz o job falhar se houver vulnerabilidade conhecida em `requirements.txt` (ADR-0018).
- **`project.md`:** a linha "Auditoria de dependências" em "Comandos de verificação" passa a trazer o comando real.

**Suposições registradas:**
- A auditoria **bloqueia** o CI (falha o job) e não só avisa. Uma vulnerabilidade sem correção disponível pode ser ignorada com `--ignore-vuln <ID>`, desde que a exceção fique justificada no próprio workflow.
- O `pip-audit` roda só no CI, numa versão fixada no workflow (`pip-audit==2.10.1`), e não entra no `requirements.txt`.
- Nenhuma mudança de comportamento visível: as specs continuam válidas, e por isso `skip_specs: true`.

**Fora do escopo:**
- Rate limiting e throttling da API, que continuam como decisão registrada. Viram pré-requisito obrigatório para quando houver autenticação ou deploy.
- Varredura de secrets (ex.: `gitleaks`), que fica para uma change própria.
- Separar as dependências de desenvolvimento (pytest) das de execução.
- CSRF e XSS: os achados foram descartados na verificação, como explicado em Why.

## Capabilities

### New Capabilities
- Nenhuma.

### Modified Capabilities
- Nenhuma. O comportamento descrito nas specs não muda (`skip_specs: true`): o mascaramento de dados pessoais nos logs continua o mesmo, só fica mais rápido.

## Impact

- **Código (`C:\openspec\tarefas`):** `shared/logging.py`, `tests/shared/test_logging.py` (testes de tempo), `requirements.txt` e `.github/workflows/ci.yml`.
- **Store:** `openspec/project.md` (Comandos de verificação) e a ADR-0018 (`Proposed`).
- **Dependências:** DRF de 3.16.1 para 3.17.2 (versão menor) e pytest de 8.4.2 para 9.0.3 (versão maior, só para testes).
- **ADRs aplicáveis:** 0009 (mascaramento nos logs) e 0002 (dependências fixadas).

## Riscos

| Pergunta | Resposta |
|---|---|
| Coleta, expõe, registra em log ou retém dados pessoais ou sensíveis? | **Sim, toca no mascaramento de logs.** Uma regressão no filtro poderia deixar CPF, e-mail ou telefone em claro. Mitigação: os testes atuais do filtro continuam e passam a cobrir os limites dos quantificadores novos. |
| Altera autenticação, autorização ou superfície exposta? | **Não aplicável.** Nenhuma rota, permissão ou cabeçalho muda. A atualização do DRF não muda a configuração da API (só `JSONRenderer` e `JSONParser`). |
| Altera esquema, volume ou padrão de acesso a dados? | **Não aplicável.** Nenhum model nem migração. |
| Exige configuração, segredo ou variável de ambiente nova? | **Não aplicável.** O `pip-audit` roda no CI sem segredo. |
| Quebra compatibilidade com clientes, integrações ou dados existentes? | **Possivelmente, nos testes.** O pytest 9 é versão maior e pode exigir ajuste em testes ou fixtures. O DRF 3.17 é versão menor, sem quebra esperada na API JSON. Mitigação: rodar a suíte completa e os roteiros de navegador. |

## Aprovação

- Responsável: Pendente
- Data: —
- Escopo: —
- Condições: —
- Origem: —
