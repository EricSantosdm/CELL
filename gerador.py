import random
import json
import time
import subprocess
import os

# Função para gerar um hash aleatório (simulando o campo "cod")
def gerar_hash():
    return ''.join(random.choices('abcdef0123456789', k=40))

# Lista de cursos possíveis
cursos = [
    "Cavaleiro da Capela",
    "Cavaleiro da Salém",
    "Cavaleiro do Ébano",
    "Cavaleiro da Tríade",
    "Cavaleiro Anon",
    "Cavaleiro da Ex-Templário"
]

# Lista de status possíveis
status_list = [
    "Avaliação Pendente",
    "Avaliação Iniciada",
    "Avaliação Parcial"
]

# Lista de corretores possíveis
corretores = [
    "Bruno Vinicius de Carvalho",
    "Bruno de Cico Bataglia Cornicelli",
    "Ícaro Tadeu de Castro Xavier Lima",
    "Rodrigo Oliveira da Silva",
    "Ikaro Fachin",
    "Francisco Iago Carneiro Rodrigues",
    "Lucas Martins Diniz",
    "Eric dos Santos Bezerra",
    "Cláudio Roberto Silva Júnior"
]

# Função para gerar um dado aleatório
def gerar_dado():
    curso = random.choice(cursos)
    cod = gerar_hash()
    tempo = f"{random.randint(1, 30)} dias"  # Tempo entre 1 e 30 dias
    status = random.choice(status_list)
    corretor = random.sample(corretores, k=2)  # Seleciona 2 corretores aleatórios
    corretor = ", ".join(corretor)  # Junta os nomes dos corretores em uma string
    tipo = "normal"

    return {
        "curso": curso,
        "cod": cod,
        "tempo": tempo,
        "status": status,
        "corretor": corretor,
        "tipo": tipo
    }

# Função principal
def main():
    try:
        # Solicita ao usuário a quantidade de dados a serem gerados
        quantidade = int(input("Digite a quantidade de dados a serem gerados: "))
        
        # Gera a quantidade especificada de dados
        dados_teste = [gerar_dado() for _ in range(quantidade)]
        
        # Exibe os dados no console
        print(json.dumps(dados_teste, indent=2))
        
        # Salva os dados em um arquivo JSON
        with open('dados.json', 'w', encoding='utf-8') as f:
            json.dump(dados_teste, f, ensure_ascii=False, indent=2)
        
        print(f"\n{quantidade} dados gerados e salvos em 'dados.json'.")
    
    except ValueError:
        print("Por favor, insira um número válido.")

# Executa o script
if __name__ == "__main__":
    main()

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