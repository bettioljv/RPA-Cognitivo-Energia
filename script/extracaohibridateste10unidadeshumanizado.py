import time
import logging
from seleniumbase import SB
from selenium.webdriver.common.by import By
from curl_cffi import requests as cffi_requests
import sys
from pathlib import Path

# Garante que o Python ache a pasta 'script' e 'core'
sys.path.append(str(Path(__file__).parent.parent))

from script.pipeline import click_pipeline
from script.type import human_type
from script.wait import human_wait
from script.utils import cursor_check_init

logging.basicConfig(filename='relatorio_10_unidades.log', level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
LOCKED_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"

def is_valid_pdf(file_content):
    if len(file_content) < 100: return False
    if file_content.startswith(b'%PDF'): return True
    return False

def testar_10_unidades_humanizado(lista_unidades):
    print("=== INICIANDO TESTE DE ESTRESSE HUMANIZADO: 10 UNIDADES ===")
    cookies_sessao = {}
    
    with SB(uc=True, headless=False, agent=LOCKED_USER_AGENT) as sb:
        driver = sb.driver
        try:
            driver.get("https://www.enel.com.br/pt-ceara/login.html")
            time.sleep(4)
            
            cursor_check_init(driver)
            
            user_el = driver.find_element(By.CSS_SELECTOR, "input[name='username']")
            cx, cy = click_pipeline(driver, user_el)
            human_type(user_el, "login_master@email.com", avg_cpm=250.0)
            human_wait("click_to_type")
            
            pass_el = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            cx, cy = click_pipeline(driver, pass_el, prev_cursor_x=cx, prev_cursor_y=cy)
            human_type(pass_el, "senha123", avg_cpm=200.0)
            human_wait("visual_search")
            
            btn_el = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            click_pipeline(driver, btn_el, prev_cursor_x=cx, prev_cursor_y=cy)
            
            time.sleep(7) 
            cookies_sessao = {c['name']: c['value'] for c in driver.get_cookies()}
            print("✅ Login Master concluído. Cookies blindados extraídos!")
            
        except Exception as e:
            print(f"❌ Falha Crítica no Login Master. Erro: {e}")
            return

    print("\n[Etapa 2] Iniciando extração híbrida em lote (Mantendo Cookies)...")
    sessao_http = cffi_requests.Session(impersonate="chrome110")
    sessao_http.cookies.update(cookies_sessao)
    sessao_http.headers.update({"User-Agent": LOCKED_USER_AGENT})
    
    sucessos, falhas = 0, 0

    for index, unidade in enumerate(lista_unidades[:10], start=1):
        print(f"\n--- Processando Unidade {index}/10: {unidade} ---")
        try:
            url_fatura = f"https://www.enel.com.br/api/fatura/download?unidade={unidade}"
            response = sessao_http.get(url_fatura, timeout=10)
            
            if response.status_code == 200 and is_valid_pdf(response.content):
                print(f"   ✅ Sucesso! Fatura {unidade} validada.")
                logging.info(f"Unidade {unidade}: SUCESSO.")
                sucessos += 1
            else:
                print(f"   ❌ Falha Específica: Erro ou Falso Positivo ({response.status_code}).")
                logging.error(f"Unidade {unidade}: FALHA - Status {response.status_code}.")
                falhas += 1
        except Exception as e:
            print(f"   ❌ Falha Específica: Queda de Conexão.")
            falhas += 1
        time.sleep(1.5) 
        
    print(f"\n=== RESUMO FINAL ===\nTotal: 10 | Sucessos: {sucessos} | Falhas: {falhas}")

if __name__ == "__main__":
    testar_10_unidades_humanizado([f"UC_{1000+i}" for i in range(10)])