---
id: ADR-0009
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0009: Controles de LGPD — anonimização em logs e criptografia de campos sensíveis

## Contexto

O produto coleta e processa dados pessoais de proprietários e moradores (nome, e-mail, CPF), sujeitos à LGPD. Os logs vão para stdout, e o banco é self-hosted sem criptografia gerenciada.

## Decisão

- Dados pessoais MUST ser anonimizados ou mascarados em logs e relatórios. Changes MUST NOT registrar em log nome, e-mail, CPF ou outros identificadores pessoais em claro.
- Campos sensíveis (no mínimo CPF) SHALL ser criptografados na aplicação antes de persistir. A chave MUST vir de variável de ambiente e MUST NOT ser versionada.
- Busca ou unicidade por campo criptografado, quando necessária, SHALL usar um hash determinístico separado, definido no design da change.
- Toda change que coletar, expor ou reter dado pessoal MUST declarar isso na seção de riscos da proposal (regra já presente no `config.yaml`).

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Consentimento explícito com registro de aceite | Não escolhido para o MVP |
| Direito de exclusão (right to erasure) | Não escolhido para o MVP |
| Exportação de dados (portabilidade) | Não escolhido para o MVP |
| Todos os controles | O dev selecionou apenas anonimização em logs e relatórios |
| Criptografia gerenciada pela plataforma | Banco self-hosted, sem plataforma gerenciada |

## Consequências

- Mais fácil: vazamento de logs não expõe dados pessoais; dump do banco não expõe CPF em claro.
- Mais difícil: consultas e ordenação por campos criptografados; rotação de chave exige migração dos dados.
- Risco aceito: consentimento, exclusão e portabilidade não estão no MVP; sem autenticação (ADR-0005), não há controle de quem acessa os dados. O sistema MUST NOT receber dados pessoais reais enquanto essas lacunas existirem.
