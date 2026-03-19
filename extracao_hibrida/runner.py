# human_browser/runner.py
"""
HumanRunner - Executa scripts de portais existentes com infraestrutura humanizada.

O runner:
1. Configura proxy rotativo
2. Faz warmup com tls-client (captura cookies)
3. Inicia Selenium com anti-detecção
4. Injeta driver/wait no script do portal
5. Executa o script original SEM MODIFICAÇÕES

Uso:
    from human_browser import HumanRunner
    
    runner = HumanRunner()
    runner.configure(proxy_provider="brightdata", credentials={...})
    runner.run_script("scripts/portal_equatorial.py", {
        "unidade_consumidora": "123456",
        "cpf": "12345678901",
        ...
    })
"""

import os
import sys
import time
import runpy
import traceback
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Imports que funcionam tanto como módulo quanto execução direta
try:
    from core import (
        HumanBrowser,
        BrowserConfig,
        ProxyManager,
        ProxyConfig,
        HAS_TLS_CLIENT
    )
except ImportError:
    from .core import (
        HumanBrowser,
        BrowserConfig,
        ProxyManager,
        ProxyConfig,
        HAS_TLS_CLIENT
    )


@dataclass
class RunnerConfig:
    """Configuração do runner."""
    # Browser
    headless: bool = False
    download_dir: str = "./downloads"
    window_size: tuple = (1920, 1080)
    
    # Anti-detecção
    use_undetected: bool = True
    use_stealth: bool = True
    
    # TLS Warmup
    use_tls_warmup: bool = True
    warmup_url: Optional[str] = None  # URL para warmup (ex: página inicial do portal)
    
    # Proxy
    use_proxy: bool = True
    proxy_provider: Optional[str] = None  # brightdata, smartproxy, etc
    proxy_credentials: Dict[str, str] = field(default_factory=dict)
    
    # Timeouts
    page_load_timeout: int = 30
    implicit_wait: int = 10
    explicit_wait: int = 20
    
    # Retry
    max_retries: int = 3
    retry_delay: float = 5.0


class HumanRunner:
    """
    Runner principal que executa scripts de portais.
    
    Exemplo de uso:
    
        runner = HumanRunner()
        
        # Configura (opcional - pode usar valores padrão)
        runner.config.download_dir = "./faturas"
        runner.config.use_proxy = False  # Para testes
        
        # Executa script passando variáveis
        result = runner.run_script(
            script_path="scripts/portal_equatorial.py",
            variables={
                "unidade_consumidora": "1234567890",
                "cpf": "12345678901",
                "data_nascimento": "01/01/1990",
                "ano_fatura": "2025",
                "mes_fatura": "1"
            },
            warmup_url="https://goias.equatorialenergia.com.br/"
        )
    """
    
    def __init__(self, config: Optional[RunnerConfig] = None):
        self.config = config or RunnerConfig()
        self.proxy_manager: Optional[ProxyManager] = None
        self.browser: Optional[HumanBrowser] = None
        
        # Estado
        self._is_running = False
        self._current_script: Optional[str] = None
    
    def setup_proxy(
        self,
        provider: Optional[str] = None,
        credentials: Optional[Dict[str, str]] = None,
        proxy_list: Optional[List[Dict]] = None
    ):
        """
        Configura o proxy manager.
        
        Args:
            provider: Nome do provedor (brightdata, smartproxy, oxylabs, iproyal)
            credentials: Dict com username, password, zone (opcional)
            proxy_list: Lista manual de proxies [{"host": ..., "port": ..., ...}]
        """
        self.proxy_manager = ProxyManager()
        
        if provider and credentials:
            self.proxy_manager.configure_provider(provider, **credentials)
            print(f"✓ Proxy configurado: {provider}")
        elif proxy_list:
            self.proxy_manager.add_proxies_from_list(proxy_list)
            print(f"✓ {len(proxy_list)} proxies adicionados")
        else:
            print("⚠ Nenhum proxy configurado")
    
    def setup_free_proxies(self, count: int = 10, test_limit: int = 100):
        """
        Configura com proxies gratuitos.
        
        Args:
            count: Número de proxies desejados
            test_limit: Máximo de proxies a testar
        """
        try:
            from free_proxies import get_working_proxies
        except ImportError:
            from .free_proxies import get_working_proxies
        
        print(f"🔍 Buscando {count} proxies gratuitos...")
        proxies = get_working_proxies(count=count, test_limit=test_limit)
        
        if proxies:
            self.proxy_manager = ProxyManager()
            for p in proxies:
                self.proxy_manager.add_proxy(ProxyConfig(
                    host=p.host,
                    port=p.port,
                    protocol=p.protocol
                ))
            print(f"✓ {len(proxies)} proxies gratuitos configurados")
        else:
            print("⚠ Nenhum proxy gratuito encontrado")
            self.proxy_manager = ProxyManager()
    
    def _create_browser(self) -> HumanBrowser:
        """Cria instância do HumanBrowser com as configurações."""
        browser_config = BrowserConfig(
            headless=self.config.headless,
            window_size=self.config.window_size,
            download_dir=self.config.download_dir,
            use_undetected=self.config.use_undetected,
            use_stealth=self.config.use_stealth,
            page_load_timeout=self.config.page_load_timeout,
            implicit_wait=self.config.implicit_wait,
            explicit_wait=self.config.explicit_wait
        )
        
        pm = self.proxy_manager or ProxyManager()
        
        return HumanBrowser(browser_config, pm)
    
    def _do_warmup(self, browser: HumanBrowser, url: str) -> bool:
        """Faz o warmup TLS."""
        if not self.config.use_tls_warmup:
            return True
        
        if not HAS_TLS_CLIENT:
            print("⚠ tls-client não instalado, pulando warmup")
            return True
        
        print(f"🔥 Warmup TLS: {url}")
        return browser.warmup_session(url)
    
    def run_script(
        self,
        script_path: str,
        variables: Dict[str, Any],
        warmup_url: Optional[str] = None,
        use_proxy: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Executa um script de portal com a infraestrutura humanizada.
        
        O script recebe as variáveis injetadas no namespace global,
        incluindo 'driver' e 'wait' já configurados.
        
        Args:
            script_path: Caminho para o script Python do portal
            variables: Dicionário de variáveis para injetar no script
                      Ex: {"unidade_consumidora": "123", "cpf": "456", ...}
            warmup_url: URL para warmup TLS (página inicial do portal)
            use_proxy: Sobrescreve config.use_proxy se especificado
        
        Returns:
            Dict com resultado: {"success": bool, "error": str|None, "duration": float}
        """
        script_path = Path(script_path)
        if not script_path.exists():
            return {
                "success": False,
                "error": f"Script não encontrado: {script_path}",
                "duration": 0
            }
        
        # Configurações
        should_use_proxy = use_proxy if use_proxy is not None else self.config.use_proxy
        warmup = warmup_url or self.config.warmup_url
        
        start_time = time.time()
        self._is_running = True
        self._current_script = str(script_path)
        
        print("\n" + "=" * 60)
        print(f"🚀 Executando: {script_path.name}")
        print("=" * 60)
        
        try:
            # Cria browser
            self.browser = self._create_browser()
            
            # Inicia browser
            print(f"🌐 Iniciando browser (proxy: {should_use_proxy})")
            self.browser.start(use_proxy=should_use_proxy)
            
            # Warmup TLS
            if warmup:
                self._do_warmup(self.browser, warmup)
            
            # Prepara variáveis para injetar no script
            # O script mantém seus próprios imports, só injetamos driver, wait e as variáveis
            inject_vars = {
                # Necessário para imports funcionarem no exec()
                "__builtins__": __builtins__,
                
                # Driver e Wait já configurados
                "driver": self.browser.driver,
                "wait": self.browser.wait,
                
                # Funções humanizadas (opcionais)
                "human_delay": self.browser.human_delay,
                "human_type": self.browser.human_type,
                
                # Variáveis do usuário (do CSV)
                **variables
            }
            
            # Lê o script
            script_content = script_path.read_text(encoding='utf-8')
            
            # Remove linhas que criam driver/wait e variáveis que vamos injetar
            script_content = self._preprocess_script(script_content, list(variables.keys()))
            
            # Mostra variáveis que serão usadas (mascara senhas)
            print(f"📋 Variáveis injetadas:")
            for k, v in variables.items():
                if 'senha' in k.lower() or 'password' in k.lower():
                    print(f"   • {k}: ****")
                else:
                    print(f"   • {k}: {v}")
            
            # Executa o script
            print(f"▶ Executando script...")
            exec(script_content, inject_vars)
            
            duration = time.time() - start_time
            print(f"\n✅ Script concluído em {duration:.2f}s")
            
            return {
                "success": True,
                "error": None,
                "duration": duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"\n❌ Erro: {error_msg}")
            traceback.print_exc()
            
            return {
                "success": False,
                "error": error_msg,
                "duration": duration
            }
            
        finally:
            # Cleanup
            self._is_running = False
            self._current_script = None
            
            if self.browser:
                try:
                    self.browser.stop()
                except:
                    pass
                self.browser = None
    
    def _preprocess_script(self, script_content: str, injected_vars: list = None) -> str:
        """
        Preprocessa o script removendo APENAS o necessário:
        - Criação do driver (usamos o nosso)
        - Criação do wait (usamos o nosso) 
        - Definições das variáveis que vamos injetar
        - driver.quit() (gerenciamos nós)
        - Imports e configs que não existem no contexto
        
        O resto do script permanece INTACTO.
        """
        if injected_vars is None:
            injected_vars = []
        
        lines = script_content.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            skip_line = False
            
            # 1. Pula criação do driver
            if 'webdriver.Chrome(' in line and 'driver' in line and '=' in line:
                skip_line = True
            
            # 2. Pula criação do wait
            if 'WebDriverWait(' in line and 'wait' in line and '=' in line:
                skip_line = True
            
            # 3. Pula driver.quit()
            if 'driver.quit()' in line:
                skip_line = True
            
            # 4. Pula definições das variáveis que vamos injetar
            for var_name in injected_vars:
                # Padrão: variavel = 'valor' ou variavel = "valor"
                if stripped.startswith(f"{var_name} =") or stripped.startswith(f"{var_name}="):
                    skip_line = True
                    break
            
            # 5. Pula imports de configs que não existem
            if 'import configs' in line:
                skip_line = True
            if 'configs.CAMINHO' in line or 'configs.' in line:
                skip_line = True
            if 'os.makedirs(configs' in line:
                skip_line = True
            if 'sys.path.append' in line and 'parent.parent' in line:
                skip_line = True
            
            if not skip_line:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def run_with_script_fallback(
        self,
        scripts: list,
        variables: Dict[str, Any],
        warmup_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executa tentando múltiplos scripts em sequência.
        
        Se o primeiro script falhar, tenta o segundo, e assim por diante.
        Só passa para o próximo cliente quando todos os scripts falharem.
        
        Args:
            scripts: Lista de caminhos de scripts para tentar
            variables: Variáveis para injetar no script
            warmup_url: URL para warmup TLS
        
        Returns:
            Resultado da execução (sucesso ou último erro)
        """
        if isinstance(scripts, str):
            scripts = [scripts]
        
        # Filtra apenas scripts que existem
        scripts_existentes = []
        for s in scripts:
            if Path(s).exists():
                scripts_existentes.append(s)
            else:
                print(f"⚠️  Script não encontrado, pulando: {s}")
        
        if not scripts_existentes:
            return {
                "success": False,
                "error": "Nenhum script válido encontrado",
                "duration": 0
            }
        
        total_scripts = len(scripts_existentes)
        last_result = None
        
        for i, script_path in enumerate(scripts_existentes, 1):
            script_name = Path(script_path).name
            
            print(f"\n{'='*60}")
            print(f"📄 Script {i}/{total_scripts}: {script_name}")
            print(f"{'='*60}")
            
            result = self.run_script(
                script_path=script_path,
                variables=variables,
                warmup_url=warmup_url
            )
            
            if result["success"]:
                result["script_used"] = script_name
                return result
            
            last_result = result
            last_result["script_tried"] = script_name
            
            if i < total_scripts:
                print(f"\n❌ Script {script_name} falhou")
                # Delay aleatório entre tentativas
                import random
                delay = random.uniform(self.config.retry_delay * 0.5, self.config.retry_delay * 1.5)
                print(f"⏳ Aguardando {delay:.1f}s antes de tentar próximo script...")
                time.sleep(delay)
                
                # Rotaciona proxy se disponível
                if self.proxy_manager and self.proxy_manager.proxies:
                    self.proxy_manager.get_proxy(rotate=True)
                    print("🔄 Proxy rotacionado")
        
        print(f"\n❌ Todos os {total_scripts} scripts falharam para este cliente")
        return last_result
    
    def run_script_with_retry(
        self,
        script_path: str,
        variables: Dict[str, Any],
        warmup_url: Optional[str] = None,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executa script com retry em caso de falha.
        
        DEPRECATED: Use run_with_script_fallback com lista de scripts.
        Mantido para compatibilidade.
        """
        # Converte para o novo método
        return self.run_with_script_fallback(
            scripts=[script_path],
            variables=variables,
            warmup_url=warmup_url
        )
    
    def run_for_multiple(
        self,
        scripts: list,
        variables_list: List[Dict[str, Any]],
        warmup_url: Optional[str] = None,
        delay_between: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Executa scripts para múltiplas credenciais/configurações.
        
        Para cada cliente (linha do CSV):
        1. Tenta o primeiro script
        2. Se falhar, tenta o segundo
        3. Se falhar, tenta o terceiro
        4. Só depois passa para o próximo cliente
        
        Args:
            scripts: Lista de caminhos de scripts (ou string única)
            variables_list: Lista de dicts de variáveis (cada item = 1 cliente)
            warmup_url: URL para warmup
            delay_between: Delay entre clientes (segundos)
        
        Returns:
            Lista de resultados
        """
        # Compatibilidade: aceita string ou lista
        if isinstance(scripts, str):
            scripts = [scripts]
        
        results = []
        total = len(variables_list)
        total_scripts = len(scripts)
        
        print(f"\n{'='*60}")
        print(f"🔄 Executando para {total} clientes")
        print(f"📄 {total_scripts} script(s) disponível(is) por cliente")
        print(f"{'='*60}")
        
        for i, variables in enumerate(variables_list, 1):
            # Identifica o cliente
            cliente_id = variables.get('id') or variables.get('ID') or f"#{i}"
            print(f"\n{'#'*60}")
            print(f"👤 Cliente {i}/{total}: {cliente_id}")
            print(f"{'#'*60}")
            
            result = self.run_with_script_fallback(
                scripts=scripts,
                variables=variables,
                warmup_url=warmup_url
            )
            
            result["variables"] = variables
            result["cliente_id"] = cliente_id
            results.append(result)
            
            # Mostra resultado
            if result["success"]:
                script_usado = result.get("script_used", "?")
                print(f"\n✅ Cliente {cliente_id}: SUCESSO (script: {script_usado})")
            else:
                print(f"\n❌ Cliente {cliente_id}: FALHOU após {total_scripts} tentativa(s)")
            
            # Delay entre clientes
            if i < total:
                print(f"\n⏳ Aguardando {delay_between}s antes do próximo cliente...")
                time.sleep(delay_between)
        
        # Resumo final
        sucessos = sum(1 for r in results if r["success"])
        falhas = total - sucessos
        
        print(f"\n{'='*60}")
        print(f"📊 RESUMO FINAL")
        print(f"{'='*60}")
        print(f"   ✅ Sucessos: {sucessos}/{total}")
        print(f"   ❌ Falhas: {falhas}/{total}")
        print(f"{'='*60}")
        
        return results


# =============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# =============================================================================

def run_portal_script(
    script_path: str,
    variables: Dict[str, Any],
    warmup_url: Optional[str] = None,
    download_dir: str = "./downloads",
    use_proxy: bool = False,
    use_free_proxies: bool = False,
    headless: bool = False
) -> Dict[str, Any]:
    """
    Função de conveniência para executar um script de portal.
    
    Exemplo:
        from human_browser.runner import run_portal_script
        
        result = run_portal_script(
            script_path="scripts/portal_equatorial.py",
            variables={
                "unidade_consumidora": "123456",
                "cpf": "12345678901",
                "data_nascimento": "01/01/1990",
                "ano_fatura": "2025",
                "mes_fatura": "1"
            },
            warmup_url="https://goias.equatorialenergia.com.br/",
            download_dir="./faturas"
        )
    """
    runner = HumanRunner()
    runner.config.download_dir = download_dir
    runner.config.headless = headless
    runner.config.use_proxy = use_proxy
    
    if use_free_proxies:
        runner.setup_free_proxies()
    
    return runner.run_script(
        script_path=script_path,
        variables=variables,
        warmup_url=warmup_url
    )