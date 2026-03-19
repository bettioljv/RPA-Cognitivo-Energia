import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from script.cursor import get_cursor_position, inject_cursor_tracker

def cursor_check_init(driver, prev_cursor_x=0, prev_cursor_y=0):
    """
    Verifica se, no momento atual, na instância Selenium, existe uma
    instância de cursor simulada. Se não houver, essa é inicializada.

    Args:
        driver:
            Instância do Selenium WebDriver.
        
        prev_cursor_x (int, optional): 
            Recebe coordenada X prévia do mouse (usada para permanência
            de posicionamento de cursor pós troca de página).
            Default = 0.
        
        prev_cursor_y (int, optional):
            Recebe coordenada Y prévia do mouse (usada para permanência
            de posicionamento de cursor pós troca de página).
            Default = 0.
    """
    cursor_pos = get_cursor_position(driver)
    if cursor_pos == None:
        inject_cursor_tracker(
            driver, 
            debug=True, 
            start_x=prev_cursor_x, 
            start_y=prev_cursor_y
        )

def is_element_in_viewport(driver: WebDriver, element: WebElement) -> bool:
    """
    Verifica se o elemento está completamente visível dentro da viewport atual,
    sem necessidade de rolagem.

    Primeiro garante que o elemento está visível via Selenium e, em seguida,
    usa JavaScript para validar se seus limites estão totalmente dentro da
    área visível da janela do navegador.

    Args:
        driver (WebDriver):
            Instância ativa do Selenium WebDriver.

        element (WebElement):
            Elemento que será verificado quanto à visibilidade na viewport.

    Returns:
        bool: True se o elemento estiver totalmente dentro da área visível
        da janela; caso contrário, False.
    """
    if not element.is_displayed():
        return False

    return driver.execute_script(
        """
        const rect = arguments[0].getBoundingClientRect();
        const vh = window.innerHeight || document.documentElement.clientHeight;
        const vw = window.innerWidth || document.documentElement.clientWidth;

        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= vh &&
            rect.right <= vw
        );
        """,
        element
    )



def is_element_enabled_and_clickable(driver: WebDriver, element: WebElement) -> bool:
    """
    Verifica se um elemento está realmente pronto para receber um clique.

    A função realiza validações em duas camadas:

    1) Verificações do Selenium
       - Confirma se o elemento está visível no DOM (`is_displayed()`).
       - Confirma se o elemento não está desabilitado (`is_enabled()`).

    2) Verificações no navegador via JavaScript
       - Obtém o estilo computado para garantir que `pointer-events` não esteja desativado.
       - Centraliza o elemento na viewport com `scrollIntoView` para evitar falhas
         causadas por elementos fora da tela.
       - Confirma que o elemento possui dimensões válidas (largura e altura > 0).
       - Calcula o ponto central do elemento.
       - Usa `document.elementFromPoint()` para verificar qual elemento está
         visualmente no topo naquele ponto da tela.  
         
    Args:
        driver (WebDriver):
            Instância ativa do Selenium WebDriver.

        element (WebElement):
            Elemento que será verificado.

    Returns:
        bool: True se o elemento estiver visível, habilitado, tiver dimensões válidas,
        aceitar eventos de ponteiro, e não estiver coberto por outro elemento; 
        caso contrário, False. 
    """
    # 1)
    if not element.is_displayed() or not element.is_enabled():
        return False

    # 2)
    return driver.execute_script("""
        const el = arguments[0];

        const style = window.getComputedStyle(el);
        if (style.pointerEvents === 'none') return false;

        el.scrollIntoView({block:'center', inline:'center'});

        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;

        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;

        const top = document.elementFromPoint(cx, cy);

        return el === top || el.contains(top);
    """, element)

def wait_for_page_load(driver, timeout=30, stable_checks=3, check_interval=0.5):
    """
    Aguarda o carregamento completo da página antes de continuar a automação.

    O processo inclui:
    1) Espera o document.readyState chegar em "complete".
    2) Caso exista jQuery, aguarda o término das requisições AJAX.
    3) Aguarda uma pequena estabilização do DOM para páginas SPA
    (React, Angular, Vue).
    4) Monitora a quantidade de elementos no DOM e aguarda até que
    permaneça estável por alguns ciclos consecutivos.
    
    Args:
        driver:
            Instância do Selenium WebDriver.
            
        timeout (int, optional): 
                Tempo máximo de espera em segundos para o carregamento
                completo da página. Padrão: 30.
            
        stable_checks (int, optional): 
                Número de verificações consecutivas necessárias
                para considerar o DOM estável. Padrão: 3.
        
        check_interval (float, optional): 
                Intervalo em segundos entre verificações de
                estabilidade do DOM. Padrão: 0.5.
    """
    wait = WebDriverWait(driver, timeout)

    # 1) Documento inicial carregado
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

    # 2) Se houver jQuery, aguarda AJAX
    try:
        wait.until(lambda d: d.execute_script("return window.jQuery !== undefined"))
        wait.until(lambda d: d.execute_script("return jQuery.active === 0"))
    except Exception:
        pass

    # 3) Aguarda DOM básico existir
    wait.until(lambda d: d.execute_script(
        "return document.body !== null && document.body.childElementCount > 0"
    ))

    # 4) Aguarda estabilização do DOM
    last_count = -1
    stable_rounds = 0
    end_time = time.time() + timeout

    while time.time() < end_time:
        count = driver.execute_script(
            "return document.getElementsByTagName('*').length"
        )

        if count == last_count:
            stable_rounds += 1
            if stable_rounds >= stable_checks:
                return
        else:
            stable_rounds = 0
            last_count = count

        time.sleep(check_interval)

    raise TimeoutError("DOM não estabilizou dentro do tempo esperado.")
