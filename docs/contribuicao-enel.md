# Contribuição na frente ENEL

## Objetivo

Investigar e automatizar etapas do acesso ao portal da ENEL para recuperação de faturas em um fluxo autorizado de teste.

## Atividades realizadas

- Estruturei e ajustei as etapas de autenticação, navegação e busca de faturas.
- Trabalhei com Selenium e SeleniumBase para localizar elementos e controlar interações.
- Implementei rotinas de apoio para cliques, digitação, espera e scroll.
- Testei a reutilização de cookies de uma sessão do navegador em requisições HTTP com `curl_cffi`.
- Adicionei validação inicial de respostas por tamanho e assinatura de PDF.
- Registrei eventos e falhas para facilitar diagnóstico durante os testes.

## Limites do escopo

Este material descreve um protótipo. Não expõe credenciais, dados de consumidores, faturas nem resultados de contas reais. A execução contra portais deve ocorrer somente com autorização.

## O que eu explicaria em uma entrevista

“Minha frente no projeto CEIA foi a ENEL. Trabalhei na automação do fluxo do portal, principalmente na interação com a interface, recuperação de sessão e tentativa de validar as faturas retornadas. A parte mais desafiadora foi lidar com páginas dinâmicas, estados de sessão e falhas de execução, então estruturei rotinas de espera, clique, digitação e logs para tornar os testes mais rastreáveis.”
