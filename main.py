import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import statistics

app = FastAPI()

# Nome do arquivo para armazenar os dados dos alunos
ARQUIVO_ALUNOS = "alunos.json"

# Defino a base modelo
class Aluno(BaseModel):
    aluno_id: int
    nome: str
    notas: dict[str, float]

# Função para carregar os dados dos alunos do arquivo
def carregar_alunos():
    try:
        with open(ARQUIVO_ALUNOS, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Função para salvar os dados dos alunos no arquivo
def salvar_alunos(alunos):
    with open(ARQUIVO_ALUNOS, "w") as file:
        json.dump(alunos, file, indent=4)

# Lista que irá armazenar os dados dos alunos
alunos = carregar_alunos()

# Endpoint para adicionar aluno e suas notas
@app.post("/add-aluno/")
def adicionar_aluno(aluno_dados: Aluno):
    # Verifica se o aluno já existe
    for aluno in alunos:
        if aluno["aluno_id"] == aluno_dados.aluno_id:
            raise HTTPException(status_code=400, detail="ID de aluno já existe")
    # Validação das notas
    for disciplina, nota in aluno_dados.notas.items():
        if nota < 0 or nota > 10:
            raise HTTPException(status_code=400, detail=f"Nota inválida para {disciplina}")
        # Arredonda para uma casa decimal
        aluno_dados.notas[disciplina] = round(nota, 1)
    # Adiciona o aluno à lista de alunos
    alunos.append(dict(aluno_dados))
    # Salva os dados dos alunos no arquivo
    salvar_alunos(alunos)
    # Retorna os dados do aluno adicionado
    return aluno_dados

# Endpoint para recuperar notas de um aluno específico pelo id
@app.get("/notas-aluno/{aluno_id}")
def notas_aluno(aluno_id: int):
    # Procura pelo aluno com o id especificado
    for aluno in alunos:
        if aluno["aluno_id"] == aluno_id:
            return aluno["notas"]
    # Se o aluno não for encontrado, retorna um erro
    raise HTTPException(status_code=404, detail="ID de aluno não encontrado")

# Endpoint para recuperar notas de uma disciplina específica
@app.get("/notas-disciplina/{disciplina}")
def notas_disciplina(disciplina: str):
    # Dicionário para armazenar as notas dos alunos na disciplina especificada
    # notas_disciplina = []
    # Percorre todos os alunos
    # for aluno in alunos:
    #   Verifica se o aluno possui nota para a disciplina especificada
    #    if disciplina in aluno["notas"]:
    #        notas_disciplina.append((aluno["nome"], aluno["notas"][disciplina]))
    notas_disciplina = [(aluno["nome"], aluno["notas"][disciplina]) for aluno in alunos if disciplina in aluno["notas"]]
    # Verifica se há notas para a disciplina
    if not notas_disciplina:
        raise HTTPException(status_code=404, detail="Nenhuma nota encontrada para a disciplina especificada")
    # Ordena as notas por nota (o segundo elemento da tupla) em ordem crescente
    notas_disciplina.sort(key=lambda x: x[1])
    # Retorna as notas ordenadas do menor para o maior
    return notas_disciplina

# Endpoint para calcular media, mediana e desvio_padrao por disciplina
@app.get("/estatisticas-disciplina/{disciplina}")
def estatisticas_disciplina(disciplina: str):
    # Cria uma nova lista chamada notas que vai armazenar as notas dos alunos na disciplina desejada
    # notas = []
    # for aluno in alunos:
    #    if disciplina in aluno["notas"]:
    #        notas.append(aluno["notas"][disciplina])
    notas = [aluno["notas"][disciplina] for aluno in alunos if disciplina in aluno["notas"]]
    # Caso não tenha notas dessa disciplina, vai apresentar a mensagem detalhada no raise
    if not notas:
        raise HTTPException(status_code=404, detail="Nenhuma nota encontrada para a disciplina especificada")
    # Utilizando a biblioteca statistics vai calcular media, mediana e desvio_padrao das notas dentro da lista notas
    media = statistics.mean(notas)
    mediana = statistics.median(notas)
    desvio_padrao = statistics.stdev(notas) if len(notas) > 1 else 0
    # Vai retornar as informações desejadas em um dicionário
    return {
        "disciplina": disciplina,
        "media": round(media, 1),
        "mediana": round(mediana, 1),
        "desvio_padrao": round(desvio_padrao, 1)
    }

#Endpoint para representa os alunos com nota abaixo de 6
@app.get("/alunos-abaixo-6/")
def desempenho_abaixo_6():
    # Cria uma nova lista que vai armazenar os alunos com nota abaixo de 6
    alunos_recuperacao = []
    # Percorre todos os alunos
    for aluno in alunos:
        for disciplina, nota in aluno["notas"].items():
            # Compara se a nota do aluno é menor que 6 e se sim
            if nota < 6.0:
                # Adiciona a lista alunos_recuperação as informações desse aluno
                alunos_recuperacao.append({
                    "aluno_id": aluno["aluno_id"],
                    "nome": aluno["nome"],
                    "disciplina": disciplina,
                    "nota": nota
            })
    # Caso não haja ao menos um aluno com nota abaixo de 6, vai mostrar a informação detalhada no raise            
    if not alunos_recuperacao:        
        raise HTTPException(status_code=404, detail="Não possui alunos com nota abaixo de 6.")
    # Retorna a lista com as informações dos alunos que possui nota abaixo de 6
    return alunos_recuperacao

# Endpoint para remover alunos sem notas em pelo menos uma disciplina
@app.delete("/remover-alunos-sem-notas/")
def remover_alunos_sem_notas():
    # Salvar em um lista apenas os alunos com notas
    # alunos_com_notas = []
    # for aluno in alunos:
    #    if aluno["notas"]:
    #        alunos_com_notas.append(aluno)
    alunos_com_notas = [aluno for aluno in alunos if aluno["notas"]]
    # Definir uma variável que carrega o número de aluno(s) sem notas
    removidos = len(alunos) - len(alunos_com_notas)
    # Mensagem de erro caso não haja alunos sem notas    
    if removidos == 0:
        raise HTTPException(status_code=404, detail="Nenhum aluno sem notas encontrado")
    # Atualiza a lista global de alunos
    alunos[:] = alunos_com_notas
    # Salva os alunos atualizados no arquivo
    salvar_alunos(alunos)
    # Retorna uma mensagem com quantos alunos foram removidos
    return {"mensagem": f"{removidos} aluno(s) removido(s) sem notas registradas"}