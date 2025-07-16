import pandas as pd
import os

# Caminho do arquivo consolidado
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
arquivo_entrada = os.path.join(BASE_DIR, 'acidentes_2007_2025.csv')

# Lê o arquivo consolidado como texto para todas as colunas
print(f'Lendo {arquivo_entrada}...')
df = pd.read_csv(arquivo_entrada, encoding='utf-8', dtype=str)

# Preserva a coluna km como string, se existir
for col in df.columns:
    if col.lower() == 'km':
        df[col] = df[col].astype(str)

# Verifica o nome exato da coluna UF (pode ser 'UF', 'Uf', etc.)
colunas = [col.upper() for col in df.columns]
if 'UF' in colunas:
    nome_col_uf = df.columns[colunas.index('UF')]
else:
    raise Exception('Coluna UF não encontrada no arquivo!')

# Separa os dados
mg = df[df[nome_col_uf] == 'MG']
outros = df[df[nome_col_uf] != 'MG']

# Remove as colunas indesejadas
colunas_remover = ['uso_solo', 'municipio', 'id']
mg = mg.drop(columns=[c for c in colunas_remover if c in mg.columns])
outros = outros.drop(columns=[c for c in colunas_remover if c in outros.columns])

# Salva os arquivos
arquivo_mg = os.path.join(BASE_DIR, 'acidentes_MG.csv')
arquivo_outros = os.path.join(BASE_DIR, 'acidentes_outros.csv')

mg.to_csv(arquivo_mg, index=False, encoding='utf-8')
outros.to_csv(arquivo_outros, index=False, encoding='utf-8')

print(f'Arquivo com dados de MG salvo em: {arquivo_mg}')
print(f'Arquivo com os demais dados salvo em: {arquivo_outros}') 