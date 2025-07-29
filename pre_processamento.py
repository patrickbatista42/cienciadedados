import os
import pandas as pd

# Diretório base (ajuste se necessário)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Anos disponíveis
anos = list(range(2007, 2026))

# Lista para armazenar DataFrames
dfs = []

for ano in anos:
    pasta = f"datatran{ano}"
    caminho_pasta = os.path.join(BASE_DIR, pasta)
    arquivo_csv = os.path.join(caminho_pasta, f"datatran{ano}.csv")
    if os.path.exists(arquivo_csv):
        print(f"Lendo: {arquivo_csv}")
        try:
            df = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8', dtype=str)
            # Preserva a coluna km como string, se existir
            for col in df.columns:
                if col.lower() == 'km':
                    df[col] = df[col].astype(str)
            df['ANO_DADOS'] = str(ano)  # Adiciona coluna do ano como string
            dfs.append(df)
        except Exception as e:
            print(f"Erro ao ler {arquivo_csv}: {e}")
            with open(arquivo_csv, 'r', encoding='utf-8', errors='replace') as f:
                for i in range(5):
                    print(f.readline().strip())
    else:
        print(f"Arquivo não encontrado: {arquivo_csv}")

# Une todos os DataFrames, alinhando colunas
if dfs:
    df_total = pd.concat(dfs, ignore_index=True, sort=True)

    # Remover colunas extras, se existirem
    cols_to_remove = ['id', 'uso_solo', 'regional', 'delegacia', 'uop', 'ano']
    cols_to_remove = [col for col in cols_to_remove if col in df_total.columns]
    if cols_to_remove:
        df_total = df_total.drop(columns=cols_to_remove)
        print(f'Colunas removidas: {cols_to_remove}')

    output_path = os.path.join(BASE_DIR, "acidentes_2007_2025.csv")
    df_total.to_csv(output_path, index=False, encoding='utf-8')
    print(f"Arquivo final salvo em: {output_path}")
else:
    print("Nenhum arquivo CSV encontrado para processar.")
