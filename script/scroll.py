"""
scroll.py

Função para simular movimentos do scroll do mouse com aparência humana
em navegação automatizada via Selenium + Chrome DevTools Protocol (CDP).

Principais características:
- Simulação de movimento de scroll do mouse humano (scroll "em partes")
- Simulação de procura do elemento alvo na página com scroll e tempos de reação realistas
"""

import random
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from script.utils import is_element_in_viewport
from script.wait import human_wait

def human_scroll(
    driver: WebDriver, 
    element: WebElement, 
    align_to: str = "center",
    step_min: int = 250,
    step_max: int = 400,
    max_attempts:int = 30
    ) -> None:
    """
    Faz scroll "humanizado" até o elemento ficar visível na viewport, em pequenos passos.
    
    Args:
        driver:
            Instância do Selenium WebDriver.

        element:
            WebElement alvo no qual será usado como referência no scroll.

        align_to (str):
            Define como o elemento será alinhado na viewport quando se tornar visível.
            Valores aceitos seguem o scrollIntoView do JavaScript:
            "start", "center", "end" ou "nearest". Default = "center".

        step_min (int):
            Quantidade mínima de pixels para cada passo de scroll parcial.

        step_max (int):
            Quantidade máxima de pixels para cada passo de scroll parcial.

        max_attempts (int):
            Número máximo de tentativas de scroll antes de interromper o processo,
            evitando loop infinito caso o elemento não seja encontrado.
    """

    for _ in range(max_attempts):
        # Simulação de tempo de procura visual por elemento na tela
        human_wait("visual_search")

        # Se elemento na tela, alinhar de acordo com 'align_to'
        if is_element_in_viewport(driver, element):
            driver.execute_script(
                """
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: arguments[1]
                });
                """,
                element,
                align_to,
            )
            # Pequena pausa final para completar o smooth scroll
            human_wait("after_scroll")
            return

        # Scroll parcial para baixo
        step = random.randint(step_min, step_max)
        driver.execute_script(
            """
            window.scrollBy({
                top: arguments[0],
                left: 0,
                behavior: 'smooth'
            });
            """,
            step,
        )

        # Pausa curta para dar tempo do smooth scroll ocorrer
        human_wait("after_scroll")
