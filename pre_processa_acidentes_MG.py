import pandas as pd
import numpy as np
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time
from tqdm import tqdm

# =============================
# 1. Carregar o CSV original
# =============================
df = pd.read_csv('acidentes_MG.csv', sep=',', encoding='utf-8')

# =============================
# 2. Limpeza e Padronização Inicial
# =============================
df_proc = df.copy()  # Evita SettingWithCopyWarning

# Colunas de texto a padronizar
txt_cols = [
    'classificacao_acidente',
    'causa_acidente',
    'condicao_metereologica',
    'tipo_acidente',
    'tracado_via'
]
for col in txt_cols:
    if col in df_proc.columns:
        df_proc[col] = (
            df_proc[col]
            .astype(str)
            .str.lower()
            .str.strip()
            .replace({'não informado': None, 'nan': None, 'none': None})
        )
        df_proc[col] = df_proc[col].replace({'^nan$': None, '^none$': None}, regex=True)

# =============================
# 3. Agrupamento de Categorias Sinônimas e Semânticas
# =============================
class_map = {
    'sem vítima': 'sem_vitimas',
    'sem vítimas': 'sem_vitimas',
    'com vítimas': 'com_vitimas_feridas',
    'com vítima': 'com_vitimas_feridas',
    'com vítimas feridas': 'com_vitimas_feridas',
    'com vítimas leves': 'com_vitimas_feridas',
    'com vítimas graves': 'com_vitimas_feridas',
    'com vítimas fatais': 'com_vitimas_fatais',
    'outros': None
}
if 'classificacao_acidente' in df_proc.columns:
    df_proc['classificacao_acidente'] = df_proc['classificacao_acidente'].replace(class_map)

# =============================
# 4. Tratamento Multi-Label: tracado_via
# =============================
if 'tracado_via' in df_proc.columns:
    # Identifica categorias base únicas
    tracado_unique = set()
    df_proc['tracado_via'] = df_proc['tracado_via'].fillna('')
    for val in df_proc['tracado_via']:
        for item in val.split(';'):
            item = item.strip()
            if item:
                tracado_unique.add(item)
    tracado_unique = sorted(tracado_unique)
    # Cria colunas binárias para cada característica
    for cat in tracado_unique:
        col_name = f"tracado_tem_{re.sub(r'[^a-z0-9]', '_', cat)}"
        df_proc[col_name] = df_proc['tracado_via'].apply(lambda x: int(cat in [i.strip() for i in x.split(';')]))

# =============================
# 5. Engenharia de Causas: causa_acidente
# =============================
def map_causa(causa):
    if pd.isnull(causa):
        return None
    causa = str(causa).lower()
    if 'álcool' in causa or 'alcool' in causa:
        return 'ingestao_de_alcool'
    if 'falta de atenção' in causa or 'ausência de reação' in causa or 'ausencia de reacao' in causa or 'celular' in causa:
        return 'falta_de_atencao'
    if 'pneu' in causa or 'freio' in causa or 'mecânica' in causa or 'mecanica' in causa:
        return 'defeito_mecanico_veiculo'
    if 'pista' in causa or 'pavimento' in causa or 'acostamento' in causa or 'sinalização' in causa or 'sinalizacao' in causa:
        return 'defeito_na_via'
    if 'pedestre' in causa:
        return 'atropelamento_pedestre'
    if 'velocidade' in causa:
        return 'velocidade_incompativel'
    return 'outras'
if 'causa_acidente' in df_proc.columns:
    df_proc['causa_acidente'] = df_proc['causa_acidente'].apply(map_causa)

# =============================
# 6. Binarização (One-Hot Encoding)
# =============================
dummies_cols = [
    'classificacao_acidente',
    'causa_acidente',
    'condicao_metereologica',
    'tipo_acidente',
    'tipo_pista',
    'sentido_via',
    'fase_dia'
]
dummies_cols = [col for col in dummies_cols if col in df_proc.columns]
df_dummies = pd.get_dummies(df_proc[dummies_cols], prefix=dummies_cols, dummy_na=False, drop_first=False)

# =============================
# 7. Variáveis Cíclicas: dia_semana
# =============================
if 'dia_semana' in df_proc.columns:
    dia_map = {
        'segunda-feira': 0, 'segunda': 0,
        'terça-feira': 1, 'terca-feira': 1, 'terça': 1, 'terca': 1,
        'quarta-feira': 2, 'quarta': 2,
        'quinta-feira': 3, 'quinta': 3,
        'sexta-feira': 4, 'sexta': 4,
        'sábado': 5, 'sabado': 5,
        'domingo': 6
    }
    df_proc['dia_semana_num'] = df_proc['dia_semana'].str.lower().map(dia_map)
    df_proc['dia_semana_sin'] = np.sin(2 * np.pi * df_proc['dia_semana_num'] / 7)
    df_proc['dia_semana_cos'] = np.cos(2 * np.pi * df_proc['dia_semana_num'] / 7)

# =============================
# 8. Finalização
# =============================
# Concatena dummies
if not df_dummies.empty:
    df_proc = pd.concat([df_proc, df_dummies], axis=1)
# Remove colunas categóricas originais
cols_to_drop = [
    'classificacao_acidente',  'condicao_metereologica',
    'tipo_acidente', 'tipo_pista', 'tracado_via', 'sentido_via', 'fase_dia', 'dia_semana', 'dia_semana_num'
]
cols_to_drop = [col for col in cols_to_drop if col in df_proc.columns]
df_proc = df_proc.drop(columns=cols_to_drop)

# Salva o resultado em um novo CSV
output_path = 'acidentes_MG_preprocessado.csv'

# =============================
# 9. Otimização de tipos: bool e int64 (0/1) para uint8
# =============================
for col in df_proc.columns:
    # Se for booleano, converte para uint8
    if df_proc[col].dtype == bool:
        df_proc[col] = df_proc[col].astype('uint8')
    # Se for int64 e só tiver 0 ou 1, converte para uint8
    elif df_proc[col].dtype == 'int64':
        uniques = df_proc[col].dropna().unique()
        if set(uniques).issubset({0, 1}):
            df_proc[col] = df_proc[col].astype('uint8')


# Exibe amostra e info do DataFrame final
print("\n=== AMOSTRA DO DATAFRAME FINAL ===")
print(df_proc.head())
print("\n=== INFORMAÇÕES DO DATAFRAME ===")
print(df_proc.info())

df_proc.to_csv(output_path, index=False, encoding='utf-8')
print(f'\nArquivo salvo em: {output_path}') 