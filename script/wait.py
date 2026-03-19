import time, random

def human_wait(context: str):
    """
    Aplica tempos de espera "humanizados" com pequena variabilidade
    para simular pausas naturais durante navegações web.

    Args:
        context (str):
            Define o tipo de interação que está acontecendo, para escolher
            um intervalo de tempo mais realista. Valores suportados:

            - "visual_search":
                Tempo de varredura visual para localizar ou confirmar um elemento na tela.

            - "cursor_to_click":
                Micro pausa após o cursor chegar ao alvo antes do clique.

            - "click_to_type":
                Pequena pausa para simular o tempo de levar a mão do mouse ao teclado.

            - "after_scroll":
                Pequena pausa após um scroll suave para aguardar a estabilização da tela.
    """

    wait_ranges = {
        # Varredura visual para localizar / confirmar elemento
        "visual_search": (0.4, 0.8),

        # Micro atraso após o cursor alcançar o alvo antes do clique
        "cursor_to_click": (0.08, 0.22),

        # Pausa cognitiva após focar input antes de digitar
        "click_to_type": (0.25, 0.7),
        
        # Pausa curta após scroll suave
        "after_scroll": (0.15, 0.35)
    }

    # Se string 'context' usada não estiver definida em 'wait_ranges', usa valor default de (0.2, 0.5)
    min_t, max_t = wait_ranges.get(context, (0.2, 0.5))
    time.sleep(random.uniform(min_t, max_t))
