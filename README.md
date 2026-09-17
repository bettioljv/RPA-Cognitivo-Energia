# Automação de Faturas de Energia

Projeto em Python para explorar automação de fluxos de faturas em portais de energia. O trabalho foi desenvolvido no contexto do **CEIA — Centro de Excelência em Inteligência Artificial**.

> **Status:** protótipo técnico em evolução. Esta versão documenta o que está presente no repositório; resultados de produção e integrações ativas não são assumidos.

## Minha contribuição — frente ENEL

Atuei na automação do portal da **ENEL**, com foco em:

- construção e ajuste do fluxo de login e navegação;
- interação com elementos da página usando Selenium/SeleniumBase;
- rotinas de clique, digitação, espera e scroll para lidar com páginas dinâmicas;
- teste de sessão híbrida: cookies obtidos no navegador e reutilizados em requisições HTTP;
- validação inicial de respostas de fatura pelo tamanho do conteúdo e assinatura `%PDF`;
- registro de logs e tratamento de falhas durante os testes.

O projeto fez parte de uma iniciativa maior de automação para concessionárias. A contribuição descrita aqui representa especificamente a minha frente de trabalho.

## Tecnologias

Python · Selenium · SeleniumBase · curl_cffi · requests

## Estrutura atual

| Caminho | Papel |
| --- | --- |
| `extracao_hibrida/` | Orquestração de lotes e executor genérico |
| `script/` | Utilitários de interação no navegador e experimento ENEL |
| `core/` | Configuração, logs e utilitários |
| `dados/exemplos/` | Entradas fictícias para demonstrar o formato esperado |

## Como preparar o ambiente

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Alguns componentes importados pelo executor genérico ainda precisam ser consolidados neste repositório. Por isso, a execução ponta a ponta deve ser validada antes de ser apresentada como funcional.

## Privacidade e uso responsável

Os arquivos de exemplo usam dados fictícios. Credenciais, CPF/CNPJ, unidades consumidoras, cookies, faturas e dados de clientes não devem ser versionados.

A automação deve ser usada somente em ambientes e contas autorizados, respeitando as regras de cada portal.

## Próximos passos

- [ ] Consolidar componentes do navegador e caminhos de importação.
- [ ] Validar um fluxo completo autorizado da ENEL, incluindo persistência do PDF.
- [ ] Adicionar testes para configuração, leitura de CSV e validação de PDF.
- [ ] Publicar uma demonstração sanitizada do fluxo e de seus logs.
- [ ] Avaliar recursos de IA para diagnóstico de falhas após estabelecer uma base determinística.

## Contexto profissional

Além deste repositório pessoal, participei de repositórios institucionais do CEIA voltados à automação de portais. A disponibilidade desses repositórios depende das permissões da organização.
