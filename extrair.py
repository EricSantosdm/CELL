from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import baseInfo as BaseInfo # Garanta que este módulo contenha USERNAME e PASSWORD

driver = webdriver.Firefox()
wait = WebDriverWait(driver, 10)

def login():
    """Realiza o login na plataforma."""
    driver.get("https://sis.demolaybrasil.org.br/login")
    
    driver.find_element(By.ID, "login").send_keys(BaseInfo.USERNAME)
    driver.find_element(By.ID, "senha").send_keys(BaseInfo.PASSWORD)
    
    print("Resolva o CAPTCHA e pressione ENTER para continuar...")
    input() # Espera o usuário resolver o CAPTCHA
    
    login_button = driver.find_element(By.XPATH, "//input[@value='Entrar' and @onclick='logar();']")
    login_button.click()
    time.sleep(5) # Tempo para a página carregar após o login

def get_pg_total(driver):
    """Obtém o número total de páginas de resultados."""
    try:
        pg_total_element = driver.find_element(By.ID, "pg_total")
        pg_total = int(pg_total_element.text) if pg_total_element.text.isdigit() else 0
    except:
        pg_total = 0
    return pg_total

def extract_data(driver, wait, buscar_xpath, next_button_xpath, retorno_id, tipo):
    """
    Extrai dados de uma aba específica da plataforma, navegando por todas as páginas.
    Retorna uma lista de dicionários, onde cada dicionário representa uma linha de dados.
    """
    buscar_button = wait.until(EC.element_to_be_clickable((By.XPATH, buscar_xpath)))
    buscar_button.click()

    time.sleep(10) # Tempo para os resultados da busca inicial carregarem

    all_data = []
    pg_total = get_pg_total(driver)

    # Definir as chaves esperadas para cada linha de dados
    expected_keys = ['curso', 'cod', 'tempo', 'status', 'corretor', 'fila']

    num_pages_to_process = pg_total if pg_total > 0 else 1 # Processa pelo menos 1 página

    for page in range(num_pages_to_process):
        print(f"Extraindo dados da página {page + 1} de {num_pages_to_process} ({tipo})...")
        
        retorno_pesquisa = driver.find_element(By.ID, retorno_id)
        html_content = retorno_pesquisa.get_attribute('innerHTML')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        rows_found_on_page = 0
        for row_div in soup.find_all('div', class_='area_pesquisap'):
            rows_found_on_page += 1
            cols = row_div.find_all('div', class_=lambda x: x and x.startswith('col_'))
            
            row_dict = {}
            for i, col_element in enumerate(cols):
                if i < len(expected_keys):
                    row_dict[expected_keys[i]] = col_element.text.strip()
            
            for key in expected_keys:
                if key not in row_dict:
                    row_dict[key] = ""
            
            row_dict['tipo'] = tipo
            
            all_data.append(row_dict)
        
        print(f"  --> Encontradas {rows_found_on_page} linhas de dados na página {page + 1} ({tipo}).")

        # Clicar no botão "Próximo" se não for a última página
        if pg_total > 0 and page < pg_total - 1:
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
            next_button.click()
            time.sleep(5) # Aguarde a próxima página carregar

    return all_data

# --- Fluxo Principal do Script ---
login()

# Extrair dados da aba "Provas"
driver.get("https://sis.demolaybrasil.org.br/ava/provas")
provas_data = extract_data(
    driver=driver,
    wait=wait,
    buscar_xpath="//input[@value='Buscar' and @onclick='pesquisar_provas();']",
    next_button_xpath="//input[@class='bt_next' and @onclick=\"pesquisar_provas('next');\"]",
    retorno_id="retorno_pesquisa",
    tipo="Normal"
)

# Extrair dados da aba "Excelência"
driver.get("https://sis.demolaybrasil.org.br/ava/excelencia")
excelencia_data = extract_data(
    driver=driver,
    wait=wait,
    buscar_xpath="//input[@value='Buscar' and @onclick='pesquisar_excelencia();']",
    next_button_xpath="//input[@class='bt_next' and @onclick=\"pesquisar_excelencia('next');\"]",
    retorno_id="retorno_pesquisa",
    tipo="Excelência"
)

# Mesclar os dados de ambas as abas
all_combined_data = provas_data + excelencia_data

print(f"\nTotal de itens coletados (provas + excelência): {len(all_combined_data)}")

# Transformar a lista de dicionários para o formato JSON desejado: { "chave_unica": { ... } }
json_output = {}
items_added_to_json = 0
for i, item in enumerate(all_combined_data):
    # Tenta usar 'fila' como chave. Se vazio, tenta 'cod'. Se ambos vazios, usa um índice.
    key = item.get('fila', '').strip()
    if not key: # Se 'fila' for vazia ou só espaços
        key = item.get('cod', '').strip()
        if not key: # Se 'cod' também for vazio
            key = f"item_{i}" # Chave de fallback única baseada no índice
            print(f"AVISO: Item {i} sem valor em 'fila' e 'cod'. Usando chave de fallback: '{key}'.")
        else:
            print(f"INFO: Item {i} sem valor em 'fila'. Usando 'cod' como chave: '{key}'.")
    
    # Converte 'tempo' para int. Se não for numérico, define como 0.
    tempo_value = item.get('tempo', '')
    try:
        tempo_value = int(tempo_value)
    except ValueError:
        tempo_value = 0 # Define como 0 se não for um número válido ou vazio

    formatted_item = {
        "curso": item.get('curso', ''),
        "cod": item.get('cod', ''),
        "tempo": tempo_value,
        "status": item.get('status', ''),
        "corretor": item.get('corretor', ''),
        "tipo": item.get('tipo', '')
    }
    
    # Adiciona o item ao JSON. Se a chave já existir, a entrada mais recente sobrescreve.
    if key in json_output:
        print(f"AVISO: Chave '{key}' duplicada encontrada. A entrada anterior será sobrescrita.")
    
    json_output[key] = formatted_item
    items_added_to_json += 1

print(f"Total de itens adicionados ao JSON: {items_added_to_json}")

# Salvar os dados no arquivo JSON
output_filename = 'dados.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=4)

print(f"\nDados extraídos e salvos em '{output_filename}' no formato JSON.")

# Fechar o navegador
driver.quit()