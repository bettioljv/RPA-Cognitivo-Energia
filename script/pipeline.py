import time
from script.scroll import human_scroll
from script.cursor import human_cursor_move_to_element
from script.wait import human_wait
from script.type import human_type
from script.cursor import get_cursor_position
from script.utils import cursor_check_init, is_element_enabled_and_clickable
        
        
def click_pipeline(driver, element, prev_cursor_x=0, prev_cursor_y=0, retries=3, retry_wait=3):
    """
    Pipeline completo a ser feito quando houver um clique:
        1. Verificar / injetar instância do mouse
        2. Scroll até elemento
        3. Mover cursor até elemento
        4. Clique no elemento
        5. Retorna última posição do cursor
    

    Args:
        driver:
            Instância do Selenium WebDriver.
            
        element:
            WebElement alvo a ser clicado.
        
        prev_cursor_x (int, optional): 
            Recebe coordenada X prévia do mouse (usada para permanência
            de posicionamento de cursor pós troca de página).
            Default = 0.
        
        prev_cursor_y (int, optional):
            Recebe coordenada Y prévia do mouse (usada para permanência
            de posicionamento de cursor pós troca de página).
            Default = 0.
            
        retries
            Quantidade de tentativas a serem feitas caso a execução
            não seja bem sucedida.
            Default = 3.
            
        retry_wait:
            Tempo a ser experado entre cada tentativa.
            Default = 3.

    Returns:
        tuple ([int, int]):
            (x, y) onde:
            - x → última coordenada horizontal em pixels da posição do cursor.
            - y → última coordenada vertical em pixels da posição do cursor.
    """

    for attempt in range(retries):
        try:
            # 1.
            cursor_check_init(driver, prev_cursor_x, prev_cursor_y)
            
            # 2.
            human_scroll(
                    driver,
                    element
                )
            
            # 3.
            if not is_element_enabled_and_clickable(driver, element):
                raise Exception("Erro: elemento não habbilitado / não clicável.")
            
            human_cursor_move_to_element(
                    driver,
                    element
                )
            
            # 4.
            human_wait("cursor_to_click")
            
            cursor_position = get_cursor_position(driver)   # Salvar antes do clique
            
            element.click()
            
            # 5.
            if cursor_position != None:
                x, y = int(cursor_position["x"]), int(cursor_position["y"])
            else:
                x = y = 0
            
            return x, y
        
        except Exception as e:
            print(f"Tentativa de clique {attempt + 1}/{retries} falhou: {e}")
            if attempt == retries-1:
                raise
            else:
                print("Esperando e tentando denovo...")
                time.sleep(retry_wait)
        
    
    
def type_pipeline(driver, element, text, prev_cursor_x=0, prev_cursor_y=0, retries=3, retry_wait=3):
    """
    Pipeline completo a ser feito quando houver um texto a ser digitado:
        1. Pipeline de clique completo (geralmente na caixa de texto) com :func:`click_pipeline`
        2. Type do texto
        3. Salvar última posição do cursor
    

    Args:
        driver:
            Instância do Selenium WebDriver.

        element:
            WebElement que receberá o texto.
        
        text (str):
            String de texto a ser digitado.
            
        retries
            Quantidade de tentativas a serem feitas caso a execução
            não seja bem sucedida.
            Default = 3.
            
        retry_wait:
            Tempo a ser experado entre cada tentativa.
            Default = 3.
        
        prev_cursor_x (int, optional): 
            Recebe coordenada X prévia do mouse (usada para permanência
            de posicionamento de cursor pós troca de página).
            Default = 0.
        
        prev_cursor_y (int, optional):
            Recebe coordenada Y prévia do mouse (usada para permanência
            de posicionamento de cursor pós troca de página).
            Default = 0.

    Returns:
        tuple ([int, int]):
            (x, y) onde:
            - x → última coordenada horizontal em pixels da posição do cursor.
            - y → última coordenada vertical em pixels da posição do cursor.
    """
    # 1.
    x, y = click_pipeline(driver, element, prev_cursor_x, prev_cursor_y, retries, retry_wait)
   
    # 2.
    human_wait("click_to_type")
    
    for attempt in range(retries):
        try:
            human_type(element, text)
            
    # 3.
            return x, y
        
        except Exception as e:
            print(f"Tentativa de type {attempt + 1}/{retries} falhou: {e}")
            if attempt == retries-1:
                raise
            else:
                print("Esperando e tentando denovo...")
                time.sleep(retry_wait)  
