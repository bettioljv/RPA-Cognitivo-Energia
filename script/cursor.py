"""
cursor.py

Utilitários para simular movimentos de mouse com aparência humana
em navegação automatizada via Selenium + Chrome DevTools Protocol (CDP).

Principais características:
- Rastreamento do cursor no DOM via JavaScript
- Movimentos suaves com aceleração/desaceleração (smoothstep clássico)
- Trajetória curva usando Bézier quadrática
- Tempo de movimento baseado na Lei de Fitts (https://pt.wikipedia.org/wiki/Lei_de_Fitts)
- Pequenas variações (jitter) de movimento e de tempo de ação
"""

import math, time, random


# ============================================================
#   Utils
# ============================================================

def get_cursor_position(driver):
    """
    Retorna a posição atual do cursor armazenada no window.__cursor.
    """
    return driver.execute_script("return window.__cursor;")


def quadratic_bezier(p0, p1, p2, t):
    """
    Calcula um ponto em uma curva Bézier quadrática.
    """
    return (
        (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0],
        (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1],
    )


def cdp_mouse_move(driver, x, y):
    """
    Move o mouse usando o Chrome DevTools Protocol.
    """
    driver.execute_cdp_cmd("Input.dispatchMouseEvent", {
        "type": "mouseMoved",
        "x": float(x),
        "y": float(y),
        "button": "none"
    })


def smoothstep(u: float) -> float:
    """
    Função smoothstep clássica.
    Garante aceleração e desaceleração suaves.
    """
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return u * u * (3.0 - 2.0 * u)


# ============================================================
#   Funções Principais
# ============================================================
    
def inject_cursor_tracker(driver, debug=True, start_x=0, start_y=0):
    """
    Inicializa e injeta um rastreador de cursor no DOM.
    Opcionalmente renderiza um ponto visual (debug).
    
    Args:
        driver:
            Instância do Selenium WebDriver.

        debug (bool):
            Se True, desenha um ponto visual seguindo o cursor.

        start_x (int | float):
            Posição inicial X do cursor virtual ao ser injetado.

        start_y (int | float):
            Posição inicial Y do cursor virtual ao ser injetado.
    """
    js = """
    (function(debug, sx, sy){
      if (!window.__cursor) {
        window.__cursor = { x: sx, y: sy };

        document.addEventListener('mousemove', function(e){
          window.__cursor.x = e.clientX;
          window.__cursor.y = e.clientY;

          if (window.__debugCursor) {
            window.__debugCursor.style.transform =
              'translate3d(' + e.clientX + 'px,' + e.clientY + 'px,0) translate(-50%,-50%)';
          }
        }, { passive: true });

        if (debug) {
          const c = document.createElement('div');
          c.id = '__debugCursor';
          c.style.position = 'fixed';
          c.style.left = '0px';      
          c.style.top = '0px';       
          c.style.width = '10px';
          c.style.height = '10px';
          c.style.borderRadius = '50%';
          c.style.background = 'red';
          c.style.pointerEvents = 'none';
          c.style.zIndex = 2147483647;
          c.style.boxShadow = '0 0 8px red';
          c.style.willChange = 'transform';
          document.body.appendChild(c);
          window.__debugCursor = c;

          window.__debugCursor.style.transform =
            'translate3d(' + sx + 'px,' + sy + 'px,0) translate(-50%,-50%)';
        }
      }
    })(arguments[0], arguments[1], arguments[2]);
    """
    driver.execute_script(js, debug, start_x, start_y)

    
def human_cursor_move_to_element(
    driver,
    element,
    fps=120,
    curve_strength=0.35, 
    jitter_px=0.35,
    a=0.08,
    b=0.12,
    min_duration=0.18,
    max_duration=1.20,
    duration_jitter=0.06,
):
    """
    Args:
        driver:
            Instância do Selenium WebDriver (Chrome).

        element:
            WebElement alvo, o cursor se move até o centro geométrico desse elemento.

        fps (int):
            Quantidade de “frames” por segundo da animação (quantos passos por segundo).
            Maior = movimento mais suave, porém mais chamadas CDP e mais CPU.
            Valores comuns: 60–144.

        curve_strength (float):
            Intensidade do arco da trajetória (curvatura da Bézier).
            Valores maiores geram curvas mais amplas.
            Valores:
            - 0.0 = linha quase reta
            - 0.2–0.6 = média humana

        jitter_px (float):
            Ruído máximo (em pixels) aplicado por passo para micro-variação.
            O jitter é “fade-out”: forte no início e tende a 0 no final para
            melhorar a precisão ao chegar no alvo.
            Típico: 0.1–0.8.

        a (float):
            Termo constante da Lei de Fitts (tempo base em segundos).
            Define um mínimo perceptual de tempo para qualquer movimento.

        b (float):
            Coeficiente da Lei de Fitts.
            Controla o quanto distância e precisão influenciam o tempo total.

        min_duration (float):
            Duração mínima do movimento (s). Evita “teleporte” em distâncias curtas.

        max_duration (float):
            Duração máxima do movimento (s). Evita movimentos lentos demais.

        duration_jitter (float):
            Variação relativa aplicada à duração final.
            Introduz variabilidade humana no tempo total do movimento.

    Returns:
        float:
            Duração final utilizada para o movimento (em segundos) (debug).
    """
    # Posição atual do cursor
    cur = get_cursor_position(driver)
    sx, sy = float(cur["x"]), float(cur["y"])

    # Adquire coordenadas e dimensões do elemento para ser usado na Lei de Fitts
    rect = driver.execute_script("""
        const r = arguments[0].getBoundingClientRect();
        return {
            x: r.left + r.width/2,
            y: r.top + r.height/2,
            w: r.width,
            h: r.height
        };
    """, element)
    
    # Validação rigorosa: se não houve retorno ou dimensões zeradas, lança erro para não clicar no "nada"
    if not rect or (rect.get('w', 0) == 0 and rect.get('h', 0) == 0):
        # Tenta pegar informações extras do elemento para o erro ser útil
        try:
            elem_text = element.text[:50]
            elem_tag = element.tag_name
        except:
            elem_text = "indisponível"
            elem_tag = "desconhecido"
            
        raise ValueError(f"Elemento (tag={elem_tag}, text='{elem_text}') tem dimensões 0x0 ou não foi renderizado. Impossível clicar.")
        
    tx, ty = float(rect["x"]), float(rect["y"])
    w, h = float(rect["w"]), float(rect["h"])

    # Distância entre o centro do elemento alvo e as coordenadas atuais no cursor
    dx, dy = tx - sx, ty - sy
    D = math.hypot(dx, dy) or 1.0

    # W gera uma aproximação da largura faz um clamp para evitar valores excessivos
    W = max(12.0, min(w, h, 120.0))

    # Duração da ação com Lei de Fitts
    ID = math.log2(D / W + 1.0)
    duration = a + b * ID
    duration = max(min_duration, min(max_duration, duration))

    # Jitter de duração
    if duration_jitter > 0:
        duration *= 1.0 + random.uniform(-duration_jitter, duration_jitter)
        duration = max(min_duration, min(max_duration, duration))

    # Bezier 
    nx, ny = -dy / D, dx / D
    bend = D * curve_strength * random.uniform(0.5, 1.2)
    cx = (sx + tx) / 2.0 + nx * bend
    cy = (sy + ty) / 2.0 + ny * bend

    # Passos
    steps = max(1, int(duration * fps))
    dt = duration / steps

    for i in range(1, steps + 1):
        # Aceleração / Desaceleração
        u = i / steps               
        t = smoothstep(u)           

        x, y = quadratic_bezier((sx, sy), (cx, cy), (tx, ty), t)

        # Jitter de estabilização de movimento
        fade = 1.0 - t
        x += random.uniform(-jitter_px, jitter_px) * fade
        y += random.uniform(-jitter_px, jitter_px) * fade

        cdp_mouse_move(driver, x, y)
        time.sleep(dt)

    return duration
