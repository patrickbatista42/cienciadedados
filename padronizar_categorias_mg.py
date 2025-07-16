import pandas as pd
import os
from difflib import get_close_matches

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
arquivo_entrada = os.path.join(BASE_DIR, 'acidentes_MG.csv')

df = pd.read_csv(arquivo_entrada, encoding='utf-8', dtype=str)

# Dicionários de valores válidos para padronização
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

# Mapeamentos manuais para aproximações comuns
mapeamentos = {
    'causa_acidente': {
        'dormindo': 'Dormiu ao volante',
        'dormiu': 'Dormiu ao volante',
        'falta de atenção ao conduzir': 'Falta de atenção',
        'falta de atencao': 'Falta de atenção',
        'alcool': 'Ingestão de álcool',
        'alcoolizado': 'Ingestão de álcool',
        'alcoolizada': 'Ingestão de álcool',
        'psicoativa': 'Ingestão de substância psicoativa',
        'animal': 'Animais na Pista',
        'desobediencia': 'Desobediência à sinalização',
        'defeito mecanico': 'Defeito mecânico no veículo',
        'defeito na via': 'Defeito na via',
        'velocidade': 'Velocidade incompatível',
        'mal sub': 'Mal súbito',
        'agressao': 'Agressão Externa',
    },
    # Adicione outros mapeamentos se necessário
}

def padronizar_dia_semana(val):
    if pd.isnull(val):
        return val
    v = str(val).strip().lower()
    if v in ['ignorado', 'ignorada']:
        return 'Outros'
    dias = {
        'segunda-feira': 'Segunda', 'segunda': 'Segunda',
        'terça-feira': 'Terça', 'terça': 'Terça',
        'quarta-feira': 'Quarta', 'quarta': 'Quarta',
        'quinta-feira': 'Quinta', 'quinta': 'Quinta',
        'sexta-feira': 'Sexta', 'sexta': 'Sexta',
        'sábado': 'Sábado', 'sabado': 'Sábado',
        'domingo': 'Domingo'
    }
    return dias.get(v, val.title())

def padronizar_condicao(val):
    if pd.isnull(val):
        return val
    v = str(val).strip().lower()
    if v in ['ignorado', 'ignorada']:
        return 'Outros'
    if 'garoa' in v or 'chuvisco' in v:
        return 'Chuva'
    if v == 'sol':
        return 'Ceu Claro'
    if 'vento' in v:
        return 'Vento forte'
    if 'nevoeiro' in v:
        return 'Outros'
    # Similaridade alta
    match = get_close_matches(val, valores_validos['condicao_metereologica'], n=1, cutoff=0.85)
    if match:
        return match[0]
    return val

def padronizar_tipo_acidente(val):
    if pd.isnull(val):
        return val
    v = str(val).strip().lower()
    if v in ['ignorado', 'ignorada']:
        return 'Outros'
    if 'atropelamento de pedestre' in v:
        return 'Atropelamento de pessoa'
    if 'queda' in v:
        return 'Queda de ocupante de veículo'
    if 'derramamento de carga' in v:
        return 'Tombamento'
    if 'colisão' in v:
        # Se não for uma das colisões válidas, vira 'Colisão'
        match = get_close_matches(val, [x for x in valores_validos['tipo_acidente'] if 'Colisão' in x], n=1, cutoff=0.85)
        if not match:
            return 'Colisão'
    # Similaridade alta
    match = get_close_matches(val, valores_validos['tipo_acidente'], n=1, cutoff=0.85)
    if match:
        return match[0]
    return 'Outros'

def padronizar_valor(val, validos, mapeamento=None, cutoff=0.85):
    if pd.isnull(val):
        return val
    v = str(val).strip()
    if v.lower() in ['ignorado', 'ignorada']:
        return 'Outros'
    if v == '':
        return v
    v_lower = v.lower()
    # Mapeamento manual
    if mapeamento:
        for k in mapeamento:
            if k in v_lower:
                return mapeamento[k]
    # Similaridade alta
    match = get_close_matches(v, validos, n=1, cutoff=cutoff)
    if match:
        return match[0]
    return v  # Mantém valor original se não for próximo

for col in df.columns:
    if col == 'dia_semana':
        print(f'Padronizando coluna: {col}')
        df[col] = df[col].apply(padronizar_dia_semana)
    elif col == 'condicao_metereologica':
        print(f'Padronizando coluna: {col}')
        df[col] = df[col].apply(padronizar_condicao)
    elif col == 'tipo_acidente':
        print(f'Padronizando coluna: {col}')
        df[col] = df[col].apply(padronizar_tipo_acidente)
    elif col == 'causa_acidente':
        print(f'Padronizando coluna: {col}')
        df[col] = df[col].apply(lambda x: padronizar_valor(x, valores_validos[col], mapeamentos.get(col)))
    elif col in valores_validos:
        print(f'Padronizando coluna: {col}')
        df[col] = df[col].apply(lambda x: padronizar_valor(x, valores_validos[col], mapeamentos.get(col)))
    else:
        # Para todas as demais colunas categóricas, padronizar ignorado/ignorada para Outros
        df[col] = df[col].apply(lambda x: 'Outros' if isinstance(x, str) and x.strip().lower() in ['ignorado', 'ignorada'] else x)

print(f'Salvando arquivo padronizado em: {arquivo_entrada}')
df.to_csv(arquivo_entrada, index=False, encoding='utf-8')
print('Concluído!') 