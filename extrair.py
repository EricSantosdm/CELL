from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import baseInfo as BaseInfo
import random
import json
import time
import subprocess
import os

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)

def login():
    # Abre pagina de login
    driver.get("https://sis.demolaybrasil.org.br/login")
    
    # Preenche informacoes de login
    driver.find_element(By.ID, "login").send_keys(BaseInfo.USERNAME)
    driver.find_element(By.ID, "senha").send_keys(BaseInfo.PASSWORD)
    
    # Espera usuario resolver CAPTCHA
    print("Resolva o CAPTCHA e pressione ENTER para continuar...")
    input()
    
    # Clica no botao de login
    login_button = driver.find_element(By.XPATH, "//input[@value='Entrar' and @onclick='logar();']")
    login_button.click()
    time.sleep(5)

def get_pg_total(driver):
    try:
        pg_total_element = driver.find_element(By.ID, "pg_total")
        pg_total = int(pg_total_element.text) if pg_total_element.text.isdigit() else 0
    except:
        pg_total = 0
    return pg_total

# Função para extrair dados de uma aba específica e salvar em JSON
def extract_and_save_data(driver, wait, buscar_xpath, next_button_xpath, retorno_id, tipo):
    # Clicar no botão "Buscar"
    buscar_button = wait.until(EC.element_to_be_clickable((By.XPATH, buscar_xpath)))
    buscar_button.click()

    # Aguardar os resultados carregarem
    time.sleep(10)  # Ajuste este tempo conforme necessário

    all_data = []

    # Obter o número total de páginas
    pg_total = get_pg_total(driver)

    if pg_total == 0:
        print(f"Extraindo dados da única página disponível ({tipo})...")
        # Extrair dados da página atual
        retorno_pesquisa = driver.find_element(By.ID, retorno_id)
        html_content = retorno_pesquisa.get_attribute('innerHTML')
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for row in soup.find_all('div', class_='area_pesquisap'):
            cols = row.find_all('div', class_=lambda x: x and x.startswith('col_'))
            row_data = [col.text.strip() for col in cols]
            row_data.append(tipo)  # Adicionar o tipo (normal ou excelencia)
            all_data.append(row_data)
    else:
        for page in range(pg_total):
            print(f"Extraindo dados da página {page + 1} de {pg_total} ({tipo})...")
            
            # Extrair os dados da página atual
            retorno_pesquisa = driver.find_element(By.ID, retorno_id)
            html_content = retorno_pesquisa.get_attribute('innerHTML')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Processar os dados da página atual e adicionar à lista geral
            for row in soup.find_all('div', class_='area_pesquisap'):
                cols = row.find_all('div', class_=lambda x: x and x.startswith('col_'))
                row_data = [col.text.strip() for col in cols]
                row_data.append(tipo)  # Adicionar o tipo (normal ou excelencia)
                all_data.append(row_data)
            
            # Clicar no botão "Próximo" se não for a última página
            if page < pg_total - 1:
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
                next_button.click()
                time.sleep(5)  # Aguarde a próxima página carregar

    return all_data

login()

# Extrair os dados da aba "Provas"
driver.get("https://sis.demolaybrasil.org.br/ava/provas")
provas_data = extract_and_save_data(
    driver=driver,
    wait=wait,
    buscar_xpath="//input[@value='Buscar' and @onclick='pesquisar_provas();']",
    next_button_xpath="//input[@class='bt_next' and @onclick=\"pesquisar_provas('next');\"]",
    retorno_id="retorno_pesquisa",
    tipo="normal"
)

# Extrair os dados da aba "Excelência"
driver.get("https://sis.demolaybrasil.org.br/ava/excelencia")
excelencia_data = extract_and_save_data(
    driver=driver,
    wait=wait,
    buscar_xpath="//input[@value='Buscar' and @onclick='pesquisar_excelencia();']",
    next_button_xpath="//input[@class='bt_next' and @onclick=\"pesquisar_excelencia('next');\"]",
    retorno_id="retorno_pesquisa",
    tipo="excelencia"
)

# Mesclar os dados das duas abas em um único DataFrame
columns = ['curso', 'cod', 'tempo', 'status', 'corretor', 'tipo']
all_data = provas_data + excelencia_data
df_all = pd.DataFrame(all_data, columns=columns)

# Converter o DataFrame para uma lista de dicionários
data_dict = df_all.to_dict(orient='records')

# Salvar os dados em um arquivo JSON formatado
with open('dados.json', 'w', encoding='utf-8') as f:
    json.dump(data_dict, f, indent=4, ensure_ascii=False)

print("Dados extraídos e salvos em 'provas_pendentes.json'")

# Obtém o diretório atual (raiz do repositório)
repo_dir = os.getcwd()

# Mensagem do commit
commit_message = 'Dados atualizados em: ' + str(time.time())

# Comandos Git
commands = [
    ['git', 'add', '.'],  # Adiciona todas as alterações
    ['git', 'commit', '-m', commit_message],  # Faz o commit
    ['git', 'push', 'origin', 'main']  # Faz o push para o branch main
]

# Executa os comandos
for command in commands:
    try:
        subprocess.run(command, cwd=repo_dir, check=True)
        print(f"Comando executado com sucesso: {' '.join(command)}")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando: {' '.join(command)}")
        print(e)
        break

# Fechar o navegador
driver.quit()