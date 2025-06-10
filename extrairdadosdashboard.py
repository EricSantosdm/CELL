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
    # A ordem é baseada na extração das 'col_' div's
    expected_keys = ['curso', 'cod', 'tempo', 'status', 'corretor', 'fila'] # 'fila' ainda é extraída, mas não será usada como chave principal no JSON final

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
            
            # Preencher chaves ausentes com string vazia para garantir a estrutura
            for key in expected_keys:
                if key not in row_dict:
                    row_dict[key] = ""
            
            # Adicionar o 'tipo' explicitamente e converter para minúsculas
            row_dict['tipo'] = tipo.lower()
            
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
    tipo="Normal" # Passa "Normal" para a função, será convertido para "normal"
)

# Extrair dados da aba "Excelência"
driver.get("https://sis.demolaybrasil.org.br/ava/excelencia")
excelencia_data = extract_data(
    driver=driver,
    wait=wait,
    buscar_xpath="//input[@value='Buscar' and @onclick='pesquisar_excelencia();']",
    next_button_xpath="//input[@class='bt_next' and @onclick=\"pesquisar_excelencia('next');\"]",
    retorno_id="retorno_pesquisa",
    tipo="Excelência" # Passa "Excelência" para a função, será convertido para "excelência"
)

# Mesclar os dados de ambas as abas
all_combined_data = provas_data + excelencia_data

print(f"\nTotal de itens coletados (provas + excelência): {len(all_combined_data)}")

# Preparar a lista final de dicionários para o JSON
final_json_list = []
items_added_to_json = 0

for item in all_combined_data:
    # Apenas os campos solicitados na saída desejada
    # 'fila' não é mais incluída no objeto final do JSON
    
    # Mantendo 'tempo' como string, como na sua saída desejada ("8 dias")
    # Removendo a conversão para int que havia antes
    
    formatted_item = {
        "curso": item.get('curso', ''),
        "cod": item.get('cod', ''),
        "tempo": item.get('tempo', ''), # Manter como string original extraída
        "status": item.get('status', ''),
        "corretor": item.get('corretor', ''),
        "tipo": item.get('tipo', '') # Já está em minúsculas da função extract_data
    }
    
    final_json_list.append(formatted_item)
    items_added_to_json += 1

print(f"Total de itens adicionados ao JSON: {items_added_to_json}")

# Salvar os dados no arquivo JSON
output_filename = 'dados.json'
with open(output_filename, 'w', encoding='utf-8') as f:
    json.dump(final_json_list, f, ensure_ascii=False, indent=4)

print(f"\nDados extraídos e salvos em '{output_filename}' no formato JSON.")

# Fechar o navegador
driver.quit()