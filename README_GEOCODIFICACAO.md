# Geocodificação de Acidentes em Minas Gerais

Este conjunto de scripts permite geocodificar dados de acidentes de trânsito em Minas Gerais, convertendo informações de rodovia, quilômetro, cidade e estado em coordenadas geográficas (latitude e longitude).

## 📋 Pré-requisitos

### Bibliotecas Python necessárias:
```bash
pip install pandas numpy geopy tqdm
```

### Arquivo de dados:
- `acidentes_MG.csv` - Arquivo com os dados de acidentes contendo as colunas:
  - `br`: Número da rodovia
  - `km`: Quilômetro da rodovia
  - `municipio`: Nome do município
  - `uf`: Sigla do estado
  - `latitude`: Coluna para latitude (pode estar vazia)
  - `longitude`: Coluna para longitude (pode estar vazia)

## 🚀 Scripts Disponíveis

### 1. `geocodificar_ultra_rapido_MG.py` ⚡ **RECOMENDADO**
**Propósito**: Processamento ultra-rápido usando base de dados local
**Tempo estimado**: ~30 segundos (para 228.233 linhas)
**Taxa de sucesso**: ~63% (cidades principais)
**Uso**: 
```bash
python geocodificar_ultra_rapido_MG.py
```

### 2. `geocodificar_hibrido_MG.py` 🔄 **MAIS COMPLETO**
**Propósito**: Base local + API complementar para máxima cobertura
**Tempo estimado**: ~5-10 minutos (dependendo das cidades não encontradas)
**Taxa de sucesso**: ~85-95%
**Uso**:
```bash
python geocodificar_hibrido_MG.py
```

### 3. `geocodificar_rapido_MG.py` ⚡
**Propósito**: Processamento otimizado com cache e agrupamento por cidade
**Tempo estimado**: ~2-3 horas (para 228.233 linhas)
**Taxa de sucesso**: ~90-95%
**Uso**:
```bash
python geocodificar_rapido_MG.py
```

### 4. `geocodificar_amostra_MG.py`
**Propósito**: Processa uma amostra de 50 linhas para teste
**Tempo estimado**: ~1 minuto
**Uso**:
```bash
python geocodificar_amostra_MG.py
```

### 5. `geocodificar_acidentes_MG.py` ⏰ **LENTO**
**Propósito**: Processa TODAS as linhas com coordenadas vazias (método original)
**Tempo estimado**: ~70 horas (para 228.233 linhas)
**Uso**:
```bash
python geocodificar_acidentes_MG.py
```

### 6. `pre_processa_acidentes_MG.py`
**Propósito**: Script completo que inclui geocodificação + processamento de dados
**Uso**:
```bash
python pre_processa_acidentes_MG.py
```

## ⚙️ Como Funciona

### Estratégias de Otimização Implementadas

#### 🚀 **Ultra-Rápido** (30 segundos)
- **Base de dados local** com coordenadas das principais cidades brasileiras
- **Processamento instantâneo** sem requisições de API
- **Taxa de sucesso**: ~63% (cidades principais)

#### 🔄 **Híbrido** (5-10 minutos)
- **Fase 1**: Base local (rápido)
- **Fase 2**: API complementar apenas para cidades não encontradas
- **Taxa de sucesso**: ~85-95%

#### ⚡ **Rápido** (2-3 horas)
- **Cache inteligente** para evitar requisições repetidas
- **Agrupamento por cidade** para processamento eficiente
- **Rate limiting otimizado** (0.5 segundos)
- **Taxa de sucesso**: ~90-95%

#### ⏰ **Original** (70 horas)
- **Geocodificação linha por linha** via API
- **Rate limiting conservador** (1.1 segundos)
- **Taxa de sucesso**: ~90-95%

### Estratégia de Geocodificação (Método Original)
O script tenta diferentes formatos de query para maximizar a taxa de sucesso:

1. `BR-{rodovia} km {km}, {cidade}, {estado}, Brasil`
2. `BR {rodovia} km {km}, {cidade}, {estado}, Brasil`
3. `{rodovia} km {km}, {cidade}, {estado}, Brasil`
4. `{cidade}, {estado}, Brasil`
5. `{cidade}, Minas Gerais, Brasil`

### Rate Limiting
- **Intervalo entre requisições**: 1.1 segundos (original) / 0.5 segundos (otimizado)
- **Limite da API Nominatim**: 1 requisição por segundo
- **Timeout**: 10 segundos por requisição (original) / 5 segundos (otimizado)

## 📊 Resultados Esperados

### Taxa de Sucesso por Método
- **Ultra-Rápido**: ~63% (cidades principais)
- **Híbrido**: ~85-95% (base local + API complementar)
- **Rápido**: ~90-95% (cache + otimizações)
- **Original**: ~90-95% (método linha por linha)

### Tempo de Processamento
- **Ultra-Rápido**: ~30 segundos
- **Híbrido**: ~5-10 minutos
- **Rápido**: ~2-3 horas
- **Original**: ~70 horas

### Formato das Coordenadas
- **Latitude**: Decimal (ex: -20.2519724)
- **Longitude**: Decimal (ex: -43.8029171)

## 🔧 Configurações

### Alterar Tamanho da Amostra
No arquivo `geocodificar_amostra_MG.py`, linha 89:
```python
tamanho_amostra = 50  # Altere este valor
```

### Alterar User Agent
Em qualquer script, linha do geolocator:
```python
geolocator = Nominatim(user_agent="seu_user_agent_aqui")
```

## ⚠️ Considerações Importantes

### Tempo de Processamento
- **228.233 linhas** ≈ **70 horas** de processamento contínuo
- **Recomendação**: Execute em partes ou use servidor dedicado

### Limitações da API
- **Nominatim**: Serviço gratuito com limitações
- **Alternativas**: Google Geocoding API, Here Geocoding API (pagas)

### Backup
- **Sempre faça backup** do arquivo original antes de executar
- O script sobrescreve o arquivo `acidentes_MG.csv`

## 🛠️ Solução de Problemas

### Erro: "ModuleNotFoundError: No module named 'geopy'"
```bash
pip install geopy
```

### Erro: "Arquivo não encontrado"
Verifique se o arquivo `acidentes_MG.csv` está no diretório correto.

### Taxa de sucesso baixa
- Verifique a qualidade dos dados de entrada
- Considere usar API paga para melhor precisão

### Processamento interrompido
- O script pode ser interrompido e executado novamente
- Ele processará apenas as linhas com coordenadas vazias

## 📈 Monitoramento

### Durante a Execução
- Barra de progresso mostra o andamento
- Contadores de sucesso/falha em tempo real
- Tempo estimado de conclusão

### Após a Execução
- Relatório detalhado de resultados
- Amostra dos dados processados
- Estatísticas de taxa de sucesso

## 🔄 Processo Recomendado

### 🚀 **Para Resultados Rápidos (Recomendado)**
1. **Execute o método ultra-rápido**:
   ```bash
   python geocodificar_ultra_rapido_MG.py
   ```

### 🔄 **Para Máxima Cobertura**
1. **Execute o método híbrido**:
   ```bash
   python geocodificar_hibrido_MG.py
   ```

### ⚡ **Para Processamento Otimizado**
1. **Execute o método rápido**:
   ```bash
   python geocodificar_rapido_MG.py
   ```

### ⏰ **Para Processamento Completo (Lento)**
1. **Execute o método original**:
   ```bash
   python geocodificar_acidentes_MG.py
   ```

## 📞 Suporte

Para dúvidas ou problemas:
- Verifique os logs de erro
- Teste com amostras menores primeiro
- Considere usar APIs pagas para melhor performance 