import os
from pathlib import Path

# ==========================================
# MAPEAMENTO DE DIRETÓRIOS
# ==========================================
# Define a raiz do projeto (Cogni_RPA_Definitivo)
BASE_DIR = Path(__file__).parent.parent.absolute()

PASTA_LOGS = BASE_DIR / "logs"
PASTA_DOWNLOADS = BASE_DIR / "faturas"
PASTA_DADOS = BASE_DIR / "dados"
PASTA_SCRIPTS = BASE_DIR / "script"

# Garante que a infraestrutura física exista (cria as pastas se faltarem)
for pasta in [PASTA_LOGS, PASTA_DOWNLOADS, PASTA_DADOS]:
    os.makedirs(pasta, exist_ok=True)

# ==========================================
# CONFIGURAÇÕES GERAIS DO MOTOR
# ==========================================
USER_AGENT_PADRAO = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
TIMEOUT_PADRAO = 30
TENTATIVAS_MAXIMAS = 3
DELAY_HUMANIZADO_BASE = 2.0

# ==========================================
# CHAVES E INTEGRAÇÕES FUTURAS
# ==========================================
# Espaço preparado para quando você for plugar o Anti-Captcha
API_KEY_CAPTCHA = os.getenv("API_KEY_CAPTCHA", "")