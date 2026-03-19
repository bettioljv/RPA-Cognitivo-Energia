import time, random

def human_type(element, text, avg_cpm=200.0, variance=0.35):
    """
    Digita texto simulando velocidade e irregularidade humanas.

    Args:
        element:
            WebElement que receberá o texto.

        text (str):
            String de texto a ser digitado.

        avg_cpm (float):
            Velocidade média de digitação em caracteres por minuto.
            Usado para calcular o atraso médio entre teclas.
            
            Possíveis valores:
            - ~200       → digitação média para adultos
            - 250-300   → digitação acima da média
            - 325–400   → digitação rápida / profissional

        variance (float):
            Fator de variação relativo do atraso entre teclas.
            0.0 = atraso constante.
            0.35 = atraso varia ±35% em torno da média.
            Deve ser >= 0.

    Returns:
        None
    """

    if avg_cpm <= 0:
        raise ValueError("avg_cpm deve ser > 0")
    if variance < 0:
        raise ValueError("variance deve ser >= 0")

    # Delay médio por key
    avg_delay = 60.0 / float(avg_cpm)   

    # Loop para cada char do texto
    for ch in text:
        element.send_keys(ch)
        delay = random.uniform(         # Delay médio + variância
            avg_delay * (1 - variance),
            avg_delay * (1 + variance),
        )
        time.sleep(max(0.0, delay))