import requests
import concurrent.futures
from dataclasses import dataclass
from typing import List

@dataclass
class ProxyConfig:
    host: str
    port: str
    protocol: str = "http"

def testar_conexao_proxy(proxy_str: str) -> ProxyConfig | None:
    """Testa se o proxy está vivo e aceitando requisições."""
    if ':' not in proxy_str:
        return None
        
    ip, port = proxy_str.split(':', 1)
    proxy_dict = {
        "http": f"http://{proxy_str}", 
        "https": f"http://{proxy_str}"
    }
    
    try:
        # Tenta bater no httpbin para validar o IP em menos de 4 segundos
        resposta = requests.get("https://httpbin.org/ip", proxies=proxy_dict, timeout=4)
        if resposta.status_code == 200:
            return ProxyConfig(host=ip, port=port)
    except Exception:
        return None
    return None

def get_working_proxies(count: int = 5, test_limit: int = 50) -> List[ProxyConfig]:
    """
    Busca, testa e retorna uma lista de proxies funcionais.
    Usado pelo runner.py para fazer a rotação de IPs.
    """
    print("🌐 Iniciando varredura por proxies gratuitos...")
    proxies_aprovados = []
    
    try:
        # Endpoint público do ProxyScrape focado no Brasil e EUA
        url_api = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000&country=BR,US&ssl=all&anonymity=all"
        resposta = requests.get(url_api, timeout=10)
        
        # Separa a lista por quebra de linha
        lista_bruta = resposta.text.strip().split('\r\n')
        candidatos = [p for p in lista_bruta if ':' in p][:test_limit]
        
        print(f"⚡ Encontrados {len(candidatos)} candidatos. Testando conexões em paralelo...")
        
        # Usa processamento paralelo para testar vários IPs ao mesmo tempo
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            resultados = executor.map(testar_conexao_proxy, candidatos)
            
            for proxy_valido in resultados:
                if proxy_valido:
                    proxies_aprovados.append(proxy_valido)
                    print(f"   [+] Proxy OK: {proxy_valido.host}:{proxy_valido.port}")
                    
                    if len(proxies_aprovados) >= count:
                        break
                        
        return proxies_aprovados
        
    except Exception as e:
        print(f"❌ Falha ao buscar proxies na rede: {e}")
        return []