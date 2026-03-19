# ⚡ RPA Cognitivo de Faturas (Híbrido + Humanizado)

Plataforma Nível Enterprise para extração em massa de faturas de energia (ENEL, CEMIG, CELESC, Equatorial) desenvolvida no escopo do **CEIA (Centro de Excelência em Inteligência Artificial)**.

## 🎯 Arquitetura
Este projeto une três tecnologias de ponta para zerar bloqueios e falhas:
1. **Agentes de IA Cognitiva:** Mapeamento semântico do DOM para autogeração de scripts (Self-Healing).
2. **Módulo de Evasão (HumanBrowser):** Simulação biométrica usando Lei de Fitts (Bézier Curves) no mouse e variação de milissegundos na digitação para burlar WAFs e Cloudflare.
3. **Extração Híbrida (`curl_cffi`):** Transferência de sessão do Selenium para requisições HTTP ultrarrápidas, validando a integridade binária do PDF em memória (Magic Number `%PDF`) em menos de 1 segundo.

## 📁 Estrutura do Repositório
* `/core`: Chassi de orquestração, logs JSON auditáveis e roteamento de proxies.
* `/script`: Módulo matemático de humanização (Cursor, Pipeline, Type).
* `/extracao_hibrida`: Motores de extração e testes de estresse com sessão contínua.
* `/dados`: Ingestão em lote (CSVs).

## 🚀 Como Executar o Teste de Estresse (Lote 10 Unidades)
Prova de conceito para manutenção de cookies e flexibilidade de exceções:
```bash
python extracao_hibrida/teste_10_unidades_humanizado.py