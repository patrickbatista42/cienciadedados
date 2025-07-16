import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
arquivo_entrada = os.path.join(BASE_DIR, 'acidentes_MG.csv')

df = pd.read_csv(arquivo_entrada, encoding='utf-8', dtype=str)

# Dicionários de valores válidos conhecidos (exemplos, podem ser expandidos)
valores_validos = {
    'classificacao_acidente': [
        'Com Vítimas Feridas', 'Com Vítimas Fatais', 'Sem Vítimas',
        'Com Vítimas', 'Sem Vítima', 'Com Vítima', 'Com Vítimas Leves', 'Com Vítimas Graves'
    ],
    'causa_acidente': [
        'Falta de atenção', 'Velocidade incompatível', 'Animais na Pista', 'Desobediência à sinalização',
        'Defeito mecânico no veículo', 'Dormiu ao volante', 'Agressão Externa', 'Mal súbito',
        'Defeito na via', 'Ingestão de álcool', 'Ingestão de substância psicoativa', 'Outras'
    ],
    'condicao_metereologica': [
        'Ceu Claro', 'Chuva', 'Nublado', 'Nevoeiro/neblina/fumaça', 'Granizo', 'Vento forte', 'Neve', 'Outros'
    ],
    'tipo_acidente': [
        'Colisão frontal', 'Colisão traseira', 'Colisão lateral', 'Colisão transversal', 'Atropelamento de animal',
        'Atropelamento de pessoa', 'Capotamento', 'Tombamento', 'Queda de ocupante de veículo', 'Saída de pista',
        'Incêndio', 'Danos eventuais', 'Engavetamento', 'Outros', 'Colisão'
    ],
    'tipo_pista': ['Dupla', 'Simples', 'Múltipla', 'Outros'],
    'tracado_via': ['Reta', 'Curva', 'Desvio temporário', 'Outros'],
    'sentido_via': ['Crescente', 'Decrescente', 'Duplo', 'Outros'],
    'fase_dia': ['Pleno dia', 'Plena noite', 'Amanhecer', 'Anoitecer', 'Outros'],
    'dia_semana': ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado'],
    'uf': ['MG'],
}

print(f"Análise de inconsistências no arquivo: {arquivo_entrada}\n")
for col in df.columns:
    if col in valores_validos:
        valores = sorted(df[col].dropna().unique())
        total = len(df)
        outros_count = (df[col] == 'Outros').sum()
        outros_perc = 100 * outros_count / total if total > 0 else 0
        validos = set([v.lower() for v in valores_validos[col]])
        encontrados = set([v.lower() for v in valores])
        inconsistentes = encontrados - validos
        if inconsistentes or outros_count > 0:
            print(f"Coluna: {col}")
            if inconsistentes:
                print(f"  >>> Valores possivelmente inconsistentes: {sorted(inconsistentes)}")
            print(f"  Total de 'Outros': {outros_count} ({outros_perc:.2f}%)")
            print('-'*70) 