import pandas as pd
import numpy as np
import re
import holidays
from tqdm import tqdm

# ==============================================================================
# PARÂMETROS DE CONFIGURAÇÃO
# ==============================================================================
GAP_THRESHOLD_KM = 0.2
ARQUIVO_ACIDENTES = 'acidentes_MG_preprocessado.csv'
ARQUIVO_RADARES = 'dados_dos_radares.csv'
ARQUIVO_SAIDA = 'dataset_final_para_ml.csv'

# ==============================================================================
# ETAPA 1: Carregar e Preparar a Base de Acidentes
# ==============================================================================
print("ETAPA 1: Carregando e preparando a base de acidentes...")
dtype_spec = {'sentido_via': str, 'tipo_acidente': str}
df_acidentes = pd.read_csv(ARQUIVO_ACIDENTES, sep=',', encoding='utf-8', dtype=dtype_spec, low_memory=False)
df_proc = df_acidentes.copy()

# Conversão de tipos
cols_to_convert_to_float = ['km', 'latitude', 'longitude']
for col in cols_to_convert_to_float:
    if col in df_proc.columns:
        df_proc[col] = df_proc[col].astype(str).str.replace(',', '.', regex=False)
        df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce')

# Feature Engineering (Severidade, Risco, Tempo)
def map_causa(causa):
    if pd.isnull(causa): return 'nao_informada'
    causa = str(causa).lower()
    if 'álcool' in causa or 'alcool' in causa: return 'ingestao_de_alcool'
    if 'falta de atenção' in causa: return 'falta_de_atencao'
    if 'velocidade' in causa: return 'velocidade_incompativel'
    return 'outras'

df_proc['data_inversa'] = pd.to_datetime(df_proc['data_inversa'], errors='coerce', dayfirst=True)
vitimas_cols = ['mortos', 'feridos_graves', 'feridos_leves']
for col in vitimas_cols:
    df_proc[col] = pd.to_numeric(df_proc[col], errors='coerce').fillna(0)

df_proc['indice_severidade'] = (df_proc['mortos'] * 5 + df_proc['feridos_graves'] * 3 + df_proc['feridos_leves'] * 1)

if 'causa_acidente' in df_proc.columns:
    df_proc['causa_agrupada'] = df_proc['causa_acidente'].apply(map_causa)
else:
    df_proc['causa_agrupada'] = 'nao_informada'

df_proc['causa_relevante_radar'] = ((df_proc['causa_agrupada'] == 'velocidade_incompativel') | (df_proc['causa_agrupada'] == 'falta_de_atencao')).astype(int)
df_proc['risco_radar'] = df_proc['indice_severidade'] * df_proc['causa_relevante_radar']

# ==============================================================================
# ETAPA 2: Segmentação Dinâmica dos Trechos de Acidente
# ==============================================================================
print(f"ETAPA 2: Segmentando BRs em trechos (gap > {GAP_THRESHOLD_KM} km)...")
df_proc.dropna(subset=['br', 'km', 'data_inversa'], inplace=True)
df_proc['br'] = df_proc['br'].astype(str).str.replace('BR-', '', regex=False).str.strip()
df_proc.sort_values(['br', 'km'], inplace=True)
km_diff = df_proc.groupby('br')['km'].diff()
new_trecho_flag = (km_diff > GAP_THRESHOLD_KM) | (km_diff.isnull())
id_trecho_numerico = new_trecho_flag.cumsum()
df_proc['id_trecho'] = 'BR' + df_proc['br'] + '_T' + id_trecho_numerico.astype(str)

# ==============================================================================
# ETAPA 3: Carregar e Preparar a Base de Radares
# ==============================================================================
print("ETAPA 3: Carregando e preparando a base de radares...")
df_radares = pd.read_csv(ARQUIVO_RADARES, sep=';', encoding='latin-1')
df_radares.columns = df_radares.columns.str.strip()
df_radares.rename(columns={'rodovia': 'br', 'km_m': 'km', 'ano_do_pnv_snv': 'ano_instalacao'}, inplace=True)
print("Filtrando radares para considerar apenas o estado de MG...")
df_radares = df_radares[df_radares['uf'].str.strip().str.upper() == 'MG'].copy()
df_radares['br'] = df_radares['br'].astype(str).str.replace('BR-', '', regex=False).str.strip()
df_radares['km'] = pd.to_numeric(df_radares['km'].astype(str).str.replace(',', '.'), errors='coerce')
df_radares['data_instalacao'] = pd.to_datetime(df_radares['ano_instalacao'].astype(str) + '-01-01', errors='coerce')
df_radares.dropna(subset=['br', 'km', 'data_instalacao'], inplace=True)

# ==============================================================================
# ETAPA 4: Calcular Impacto dos Radares Existentes (Antes/Depois)
# ==============================================================================
print("ETAPA 4: Calculando o impacto 'Antes x Depois' dos radares existentes...")
df_trechos_bounds = df_proc.groupby('id_trecho').agg(br=('br', 'first'), trecho_km_inicial=('km', 'min'), trecho_km_final=('km', 'max')).reset_index()
radares_com_trecho = []
for _, radar in df_radares.iterrows():
    trecho_match = df_trechos_bounds[(df_trechos_bounds['br'] == radar['br']) & (df_trechos_bounds['trecho_km_inicial'] <= radar['km']) & (df_trechos_bounds['trecho_km_final'] >= radar['km'])]
    if not trecho_match.empty:
        radares_com_trecho.append({'id_trecho': trecho_match.iloc[0]['id_trecho'], 'data_instalacao_radar': radar['data_instalacao']})
df_trechos_com_radar = pd.DataFrame(radares_com_trecho).drop_duplicates()
df_acidentes_enriquecido = pd.merge(df_proc, df_trechos_com_radar, on='id_trecho', how='left')
resultados_impacto = []
for id_trecho in tqdm(df_trechos_com_radar['id_trecho'].unique(), desc="Calculando Impacto"):
    resultado = {'id_trecho': id_trecho, 'reducao_pct_taxa_acidente': np.nan}
    df_analise = df_acidentes_enriquecido[df_acidentes_enriquecido['id_trecho'] == id_trecho]
    data_radar = df_analise['data_instalacao_radar'].dropna().iloc[0]
    df_antes = df_analise[df_analise['data_inversa'] < data_radar]
    df_depois = df_analise[df_analise['data_inversa'] >= data_radar]
    if not df_antes.empty and not df_depois.empty:
        anos_antes = max(1, (data_radar - df_antes['data_inversa'].min()).days / 365.25)
        anos_depois = max(1, (df_depois['data_inversa'].max() - data_radar).days / 365.25)
        taxa_acidentes_antes = len(df_antes) / anos_antes
        taxa_acidentes_depois = len(df_depois) / anos_depois
        if taxa_acidentes_antes > 0:
            resultado['reducao_pct_taxa_acidente'] = (taxa_acidentes_depois - taxa_acidentes_antes) / taxa_acidentes_antes
    resultados_impacto.append(resultado)
df_impacto = pd.DataFrame(resultados_impacto)

# ==============================================================================
# ETAPA 5: Análise de Pontos Críticos Internos aos Trechos
# ==============================================================================
print("ETAPA 5: Analisando pontos críticos dentro de cada trecho...")
severidade_por_km = df_proc.groupby(['id_trecho', 'km'])['indice_severidade'].sum().reset_index()
idx = severidade_por_km.groupby(['id_trecho'])['indice_severidade'].transform(max) == severidade_por_km['indice_severidade']
pontos_criticos_df = severidade_por_km[idx].drop_duplicates(subset='id_trecho', keep='first').rename(columns={'km': 'ponto_critico_km'})
pontos_criticos_df = pd.merge(pontos_criticos_df, df_proc[['id_trecho', 'br']].drop_duplicates(), on='id_trecho')
distancias = []
for _, trecho in tqdm(pontos_criticos_df.iterrows(), total=pontos_criticos_df.shape[0], desc="Calculando Distância Radar"):
    br_trecho = trecho['br']
    km_critico = trecho['ponto_critico_km']
    radares_na_br = df_radares[df_radares['br'] == br_trecho]
    distancia_min = np.nan
    if not radares_na_br.empty:
        distancia_min = (radares_na_br['km'] - km_critico).abs().min()
    distancias.append({'id_trecho': trecho['id_trecho'], 'distancia_radar_mais_proximo': distancia_min})
distancias_df = pd.DataFrame(distancias)

# ==============================================================================
# ETAPA 6: Gerar Dataset Final e Exibir Insights
# ==============================================================================
print("ETAPA 6: Gerando dataset final e exibindo insights...")

# Define as agregações básicas
agg_dict = {
    'br': ('br', 'first'),
    'trecho_km_inicial': ('km', 'min'),
    'trecho_km_final': ('km', 'max'),
    'trecho_densidade_acidentes': ('id_trecho', 'size'),
    'trecho_risco_total': ('risco_radar', 'sum'),
    'trecho_severidade_media': ('indice_severidade', 'mean')
}

# Identifica dinamicamente as colunas one-hot-encoded para calcular a proporção (média)
colunas_one_hot = [col for col in df_proc.columns if set(df_proc[col].dropna().unique()).issubset({0, 1}) and col not in agg_dict]

# Adiciona as colunas one-hot ao dicionário de agregação
for col in colunas_one_hot:
    agg_dict[col.replace('causa_acidente_', 'prop_causa_').replace('condicao_metereologica_', 'prop_cond_').replace('tipo_pista_', 'prop_pista_')] = (col, 'mean')

# Executa a agregação completa
df_trechos_final = df_proc.groupby('id_trecho').agg(**agg_dict).reset_index()

df_trechos_final['trecho_extensao_km'] = df_trechos_final['trecho_km_final'] - df_trechos_final['trecho_km_inicial']

# Junta todas as novas informações que criamos (ponto crítico, distância, impacto)
df_trechos_final = pd.merge(df_trechos_final, pontos_criticos_df[['id_trecho', 'ponto_critico_km']], on='id_trecho', how='left')
df_trechos_final = pd.merge(df_trechos_final, distancias_df, on='id_trecho', how='left')
df_trechos_final['tem_radar'] = df_trechos_final['id_trecho'].isin(df_trechos_com_radar['id_trecho']).astype(int)
df_trechos_final = pd.merge(df_trechos_final, df_impacto, on='id_trecho', how='left')

# Preenche valores nulos para as novas colunas
df_trechos_final['reducao_pct_taxa_acidente'].fillna(0, inplace=True)
df_trechos_final['distancia_radar_mais_proximo'].fillna(-1, inplace=True)

df_trechos_final.to_csv(ARQUIVO_SAIDA, index=False, encoding='utf-8')

# Exibir Insights
print("\n" + "="*80)
print("=== INSIGHTS FINAIS: DATASET CONSOLIDADO ===")
print("="*80)
print(f"\n[INFO] Total de trechos únicos identificados: {len(df_trechos_final)}")
print(f"[INFO] Dataset final criado com {df_trechos_final.shape[1]} colunas (features).")

print("\n--- Top 10 Trechos por Risco Total (com todas as features) ---")
cols_display = [
    'id_trecho', 'trecho_risco_total', 'trecho_extensao_km', 
    'ponto_critico_km', 'distancia_radar_mais_proximo', 'tem_radar', 'reducao_pct_taxa_acidente'
]
print(df_trechos_final.sort_values('trecho_risco_total', ascending=False).head(10)[cols_display].round(2))

print(f"\nScript concluído com sucesso. Arquivo final salvo em: '{ARQUIVO_SAIDA}'")