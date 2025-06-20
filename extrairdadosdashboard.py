from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import baseInfo as BaseInfo 

# Importar a biblioteca 2Captcha
from twocaptcha import TwoCaptcha 

driver = webdriver.Firefox()
wait = WebDriverWait(driver, 10)

# Inicializa o solver do 2Captcha com sua chave API
solver = TwoCaptcha(BaseInfo.TWOCAPTCHA_API_KEY)

def login():
    """Realiza o login na plataforma."""
    driver.get("https://sis.demolaybrasil.org.br/login")

    driver.find_element(By.ID, "login").send_keys(BaseInfo.USERNAME)
    driver.find_element(By.ID, "senha").send_keys(BaseInfo.PASSWORD)

    # --- Lógica para resolver o CAPTCHA com 2Captcha ---
    try:
        # 1. Encontrar o sitekey do reCAPTCHA na página
        # Você precisa inspecionar o elemento para obter o sitekey correto.
        # Geralmente é um div com data-sitekey.

        # Exemplo de como encontrar o sitekey (pode variar dependendo da estrutura HTML)
        # Procure por um div que contenha o reCAPTCHA, e ele terá o atributo data-sitekey
        recaptcha_div = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='g-recaptcha']")))
        sitekey = recaptcha_div.get_attribute("data-sitekey")

        if not sitekey:
            print("Erro: sitekey do reCAPTCHA não encontrado. Verifique o XPATH e a estrutura da página.")
            # Opcional: Levantar uma exceção ou sair do script
            return False 

        print(f"Sitekey do reCAPTCHA encontrado: {sitekey}")
        print("Enviando CAPTCHA para resolução pelo 2Captcha...")

        # 2. Enviar o CAPTCHA para o 2Captcha
        result = solver.recaptcha(
            sitekey=sitekey,
            url=driver.current_url # Usa a URL atual da página
        )

        recaptcha_response_token = result['code']
        print(f"CAPTCHA resolvido pelo 2Captcha. Token: {recaptcha_response_token[:30]}...") # Exibe só o começo

        # 3. Injetar o token resolvido no campo oculto do reCAPTCHA
        # O reCAPTCHA geralmente usa um textarea oculto com o ID g-recaptcha-response
        driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML = "{recaptcha_response_token}";')

        # Opcional: Se houver um checkbox "Eu não sou um robô", você pode precisar simular um clique
        # para que o reCAPTCHA entenda que foi resolvido.
        # try:
        #     # Isso pode variar. Às vezes o clique não é necessário se o token for injetado.
        #     checkbox = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-anchor")))
        #     checkbox.click()
        # except Exception as e:
        #     print(f"Não foi possível clicar no checkbox do reCAPTCHA (pode não ser necessário): {e}")

    except Exception as e:
        print(f"Erro ao resolver CAPTCHA com 2Captcha: {e}")
        # Se o CAPTCHA falhar, você pode optar por sair ou tentar novamente.
        # Por simplicidade, o script continuará, mas o login pode falhar.
        return False # Indica que o login falhou na etapa do CAPTCHA
    # --- Fim da lógica do 2Captcha ---

    login_button = driver.find_element(By.XPATH, "//input[@value='Entrar' and @onclick='logar();']")
    login_button.click()
    time.sleep(5) # Tempo para a página carregar após o login

    # Opcional: Adicionar verificação de sucesso do login
    if "login" in driver.current_url: # Ainda na página de login, significa que falhou
        print("Login falhou, provavelmente devido ao CAPTCHA ou credenciais.")
        return False
    else:
        print("Login realizado com sucesso.")
        return True


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
if login(): # Só prossegue se o login for bem-sucedido
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

    # Preparar a lista final de dicionários para o JSON
    final_json_list = []
    items_added_to_json = 0

    for item in all_combined_data:
        formatted_item = {
            "curso": item.get('curso', ''),
            "cod": item.get('cod', ''),
            "tempo": item.get('tempo', ''), 
            "status": item.get('status', ''),
            "corretor": item.get('corretor', ''),
            "tipo": item.get('tipo', '') 
        }

        final_json_list.append(formatted_item)
        items_added_to_json += 1

    print(f"Total de itens adicionados ao JSON: {items_added_to_json}")

    # Salvar os dados no arquivo JSON
    output_filename = 'dados.json'
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(final_json_list, f, ensure_ascii=False, indent=4)

    print(f"\nDados extraídos e salvos em '{output_filename}' no formato JSON.")
else:
    print("Não foi possível continuar a extração de dados devido a falha no login.")


# Fechar o navegador
driver.quit()

# Obtém o diretório atual (raiz do repositório)
repo_dir = os.getcwd()

# Mensagem do commit
commit_message = 'Meu commit automático ' + str(time.time())

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