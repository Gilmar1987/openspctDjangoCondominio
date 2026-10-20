---
id: ADR-0014
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: [cadastro-de-apartamentos]
---

# ADR-0014: Estrutura de uma fatia — domínio puro, ORM no repositório, validação Pydantic

## Contexto

Três ADRs deixaram decisões para a primeira change. A ADR-0001 pede definir onde ficam as entidades de domínio em relação aos models do ORM. A ADR-0012 pede definir como Pydantic convive com DRF e Django Forms. A decisão 5.6 exige 100% de cobertura nos módulos de domínio com TDD estrito. Essas decisões valem para todas as fatias.

## Decisão

Cada capability é um app Django. Dentro dele, a estrutura SHALL ser:

```
<app>/
  domain.py        # entidades e regras de negócio em Python puro, sem importar Django
  models.py        # models do Django ORM (persistência apenas)
  repository.py    # mapeia entidade <-> model; toda consulta parte de for_tenant()
  inputs.py        # modelos Pydantic de entrada, com mensagens em pt-BR
  features/<operação>.py   # uma fatia por operação: handler + view da API + view HTML
  urls.py, templates/<app>/
```

- `domain.py` MUST NOT importar Django, DRF ou Pydantic, e MUST ter 100% de cobertura de linhas e branches, medida no CI.
- Handlers MUST receber e devolver entidades de domínio ou tipos simples, nunca models do ORM.
- A validação de entrada SHALL ser feita só por modelos Pydantic. As views da API SHALL ser `APIView` do DRF, sem `Serializer`, e as views HTML SHALL ser views Django, sem `Form`. As duas passam os dados recebidos ao mesmo modelo Pydantic.
- Erros do Pydantic SHALL ser convertidos para pt-BR por um único tradutor compartilhado (`shared/validation.py`). Na API, o formato SHALL ser `{"errors": {"<campo>": ["<mensagem>"]}}`.
- As views HTML SHALL manter a proteção CSRF nativa do Django.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Model do ORM como entidade de domínio | Acopla regras ao banco; o TDD com 100% de cobertura exigiria banco em todo teste de domínio |
| DRF Serializers + Django Forms validando, Pydantic só no domínio | Três camadas de validação duplicadas, contrariando a ADR-0012 |
| `Serializer`/`Form` como adaptadores que chamam Pydantic | Mais código sem ganho; a renderização dos formulários é simples |
| Uma pasta por feature com vários arquivos | Arquivos demais para operações de CRUD pequenas; um módulo por operação basta |

## Consequências

- Mais fácil: testes de domínio rápidos e sem banco; mensagens de validação idênticas na API e nas páginas.
- Mais difícil: mapear manualmente entre entidade e model; perde-se o `ModelForm` e o `ModelSerializer` do Django.
- Risco aceito: as views HTML precisam renderizar os campos e os erros manualmente nos templates.
