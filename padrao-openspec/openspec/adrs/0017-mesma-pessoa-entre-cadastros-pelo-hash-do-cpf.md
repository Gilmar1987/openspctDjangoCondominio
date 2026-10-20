---
id: ADR-0017
status: Accepted
date: 2026-10-20
supersedes:
superseded_by:
related_changes: [cadastro-de-moradores]
---

# ADR-0017: Reconhecer a mesma pessoa entre cadastros pelo hash do CPF

## Contexto

Pela ADR-0016, cada entidade de pessoa (proprietário, morador e futuras) tem a sua tabela, que herda de `PersonModel`. A mesma pessoa física pode então ter mais de um cadastro. Esse risco foi aceito naquela ADR. A change `cadastro-de-moradores` exige que o sistema saiba quando um morador também é proprietário, e vice-versa. O CPF é guardado cifrado com Fernet, de forma não determinística, e com um hash HMAC determinístico (`cpf_hash`, ADR-0009). Os apps só se comunicam pelo `public.py` (ADR-0015).

## Decisão

- A identidade da mesma pessoa entre entidades de pessoa SHALL ser estabelecida pelo `cpf_hash` (HMAC-SHA256 com `CPF_HASH_KEY`), dentro do mesmo condomínio. Cadastros de condomínios diferentes MUST NOT ser relacionados.
- O hash SHALL ser calculado só por `PersonModel.hash_cpf` (`people/models.py`), com uma única `CPF_HASH_KEY` para todas as entidades. Trocar a chave exige recalcular os hashes de todas as tabelas de pessoa.
- Toda entidade de pessoa que precise ser reconhecida por outra SHALL expor no seu `public.py` uma consulta por lista de hashes, por exemplo `owners_by_cpf_hash` ou `residences_by_cpf_hash`, que devolve só identificadores e dados não pessoais.
- A comparação MUST NOT decifrar CPFs nem trafegar o CPF em claro entre apps. A única exceção é o pré-preenchimento explícito de formulário pedido pelo usuário, que copia os dados de um cadastro para outro no mesmo condomínio.
- O reconhecimento é só leitura: os dados pessoais dos cadastros MUST NOT ser sincronizados automaticamente. Cada cadastro continua independente (ADR-0016).

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Vínculo explícito (FK do morador para o proprietário) | Exige que o usuário lembre de vincular; dados copiados ficariam presos a uma FK, e o CPF poderia divergir do vinculado |
| Comparar CPFs decifrados | Decifra a tabela inteira a cada listagem e trafega CPF em claro entre apps, contra a ADR-0009 |
| Cadastro único de Pessoa com papéis | Eliminaria a duplicação, mas substitui a ADR-0016; descartado pelo responsável nesta change |

## Consequências

- Mais fácil: qualquer nova entidade de pessoa passa a se reconhecer com as existentes só expondo a consulta por hash; nenhuma tabela é decifrada.
- Mais difícil: a `CPF_HASH_KEY` vira uma dependência entre todas as tabelas de pessoa; perdê-la ou trocá-la quebra a unicidade e o reconhecimento até recalcular os hashes.
- Risco aceito: dados divergentes entre os cadastros da mesma pessoa (ex.: telefone diferente como proprietário e como morador), porque não há sincronização.
