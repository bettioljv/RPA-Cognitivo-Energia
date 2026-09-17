# Guia para interessados

## Onde está minha contribuição neste projeto?

Este repositório apresenta minha atuação na frente da **ENEL** dentro de uma iniciativa maior do **CEIA — Centro de Excelência em Inteligência Artificial**.

Os repositórios institucionais do CEIA pertencem à organização e podem ter acesso restrito. Por isso, este espaço público organiza o contexto técnico da minha contribuição sem reproduzir código institucional ou dados de clientes.

## O que desenvolvi e investiguei

- Fluxo de automação para login, navegação e busca de faturas no portal ENEL.
- Interações de navegador com Selenium e SeleniumBase.
- Funções de apoio para clique, digitação, espera e scroll em interfaces dinâmicas.
- Reaproveitamento de cookies de uma sessão de navegador em chamadas HTTP com `curl_cffi`.
- Validação inicial do retorno de documentos com verificação da assinatura `%PDF`.
- Logs e tratamento de falhas para tornar os testes reproduzíveis e rastreáveis.

## Como avaliar tecnicamente

| Área | Arquivos para começar |
| --- | --- |
| Orquestração de lote | `extracao_hibrida/run.py` |
| Executor e fallback | `extracao_hibrida/runner.py` |
| Experimento de sessão híbrida e ENEL | `script/extracaohibridateste10unidadeshumanizado.py` |
| Interações de navegador | `script/pipeline.py`, `script/cursor.py`, `script/type.py` |
| Registro de execução | `core/logger.py` |

## Escopo e transparência

Este é um protótipo técnico. O projeto não inclui credenciais, dados pessoais, faturas nem resultados de contas reais. Recursos que dependem de componentes ausentes ou de acesso a portais autorizados estão identificados no README como etapas em evolução.

## Em uma conversa técnica

Posso explicar as decisões de automação, as dificuldades de páginas dinâmicas, gestão de sessão, validação de documentos, diagnóstico de falhas e os próximos passos para transformar o protótipo em um fluxo testável de ponta a ponta.
