import pandas as pd
import os
import re
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
arquivo_entrada = os.path.join(BASE_DIR, 'acidentes_MG.csv')

print(f'Lendo {arquivo_entrada}...')
df = pd.read_csv(arquivo_entrada, encoding='utf-8', dtype=str)

# Função para padronizar número para formato brasileiro
def padronizar_numero(val):
    if pd.isnull(val) or val == '':
        return ''
    val = str(val).strip()
    # Remove pontos de milhar
    val = re.sub(r'\.(?=\d{3}(,|$))', '', val)
    # Se já tem vírgula decimal, mantém
    if re.match(r'^-?\d+,\d+$', val):
        return val
    # Se tem ponto decimal, troca por vírgula
    if re.match(r'^-?\d+\.\d+$', val):
        return val.replace('.', ',')
    # Se é inteiro
    if re.match(r'^-?\d+$', val):
        return val
    return val  # Mantém qualquer outro caso

# Padroniza todas as colunas numéricas
for col in df.columns:
    amostra = df[col].dropna().astype(str).head(100)
    if any(re.match(r'^-?\d+[\.,]?\d*$', v) for v in amostra):
        print(f'Padronizando coluna numérica: {col}')
        df[col] = df[col].apply(padronizar_numero)

# Análise e remoção de valores faltantes
missing_values = ['', 'null', 'NULL', 'na', 'NA', 'n/a', 'N/A', 'None', 'none', '-', '--', '(null)']
missing_values_lower = set([v.lower() for v in missing_values])

def is_faltante(x):
    if pd.isnull(x):
        return True
    s = str(x).strip()
    if s == '':
        return True
    if s.lower() in missing_values_lower:
        return True
    return False

# Ignorar latitude e longitude na filtragem de linhas
ignore_cols = {'latitude', 'longitude'}
cols_to_check = [col for col in df.columns if col.lower() not in ignore_cols]

total_antes = len(df)
df = df[~df[cols_to_check].apply(lambda row: any(is_faltante(x) for x in row), axis=1)]
print(f'Removidas {total_antes - len(df)} linhas com valores faltantes.')

# Exibe análise final de valores faltantes
print(f"\nAnálise de valores faltantes após limpeza:\n")
print(f"{'Coluna':<30} | {'Faltantes':>10} | {'Total':>10} | {'% Faltantes':>12}")
print('-'*70)
for col in df.columns:
    total = len(df)
    faltantes = df[col].apply(is_faltante).sum()
    perc = 100 * faltantes / total if total > 0 else 0
    print(f"{col:<30} | {faltantes:>10} | {total:>10} | {perc:>11.2f}%")

# Salva o resultado sobrescrevendo o arquivo original
print(f'Arquivo final salvo em: {arquivo_entrada}')
df.to_csv(arquivo_entrada, index=False, encoding='utf-8')
print('Concluído!') 