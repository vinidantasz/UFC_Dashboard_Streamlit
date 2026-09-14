import streamlit as st
import pandas as pd
import plotly.express as px
import kagglehub
from kagglehub import KaggleDatasetAdapter

# ------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="UFC Fight Analytics",
    page_icon="🥊",
    layout="wide"
)

# ------------------------------------------------------------
# ESTILO
# ------------------------------------------------------------
st.markdown("""
<style>
    .main > div {
        padding-top: 1.2rem;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(120, 120, 120, 0.08);
        border: 1px solid rgba(120, 120, 120, 0.18);
        padding: 14px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# CARREGAMENTO DOS DADOS
# ------------------------------------------------------------
@st.cache_data
def carregar_dados(dataset_id: str, file_path: str = ""):
    """Carrega os dados usando a API do Kaggle via `kagglehub`.

    Parâmetros:
    - dataset_id: string no formato 'owner/dataset' (ex.: 'scarekrow/ufc-data')
    - file_path: caminho opcional para um arquivo específico dentro do dataset
    """
    # Se o usuário não informou um arquivo, tentamos detectar automaticamente
    supported_exts = [
        ".csv", ".tsv", ".json", ".jsonl", ".xml", ".parquet", ".feather",
        ".sqlite", ".sqlite3", ".db", ".db3", ".s3db", ".dl3", ".xls", ".xlsx",
        ".xlsm", ".xlsb", ".odf", ".ods", ".odt"
    ]

    if not file_path:
        try:
            # Tenta usar a API oficial `kaggle` para listar arquivos do dataset
            from kaggle import KaggleApi

            api = KaggleApi()
            api.authenticate()
            listing = api.dataset_list_files(dataset_id)
            for f in listing.files:
                name = f.name if hasattr(f, "name") else str(f)
                lname = name.lower()
                for ext in supported_exts:
                    if lname.endswith(ext):
                        file_path = name
                        break
                if file_path:
                    break
        except Exception:
            # Falha ao usar a API oficial; continuará sem arquivo
            pass

    try:
        dados = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            dataset_id,
            file_path
        )
        dados["event_date"] = pd.to_datetime(dados["event_date"], errors="coerce")
        dados["year"] = dados["event_date"].dt.year
        return dados
    except Exception as e:
        st.error(f"Falha ao carregar dados via Kaggle API: {e}")
        return pd.DataFrame()

# Fonte de dados (Kaggle) - uso silencioso de valores padrão
dataset_input = "scarekrow/ufc-data"
file_path_input = ""
df = carregar_dados(dataset_input, file_path_input)

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cols = list(df.columns)
    lowermap = {c.lower(): c for c in cols}
    def find(colname):
        ln = colname.lower()
        if ln in lowermap:
            return lowermap[ln]
        key = colname.replace("_", " ").lower()
        for c in cols:
            cl = c.lower()
            if key in cl or cl.endswith(colname.split("_")[-1].lower()):
                return c
        return None
    expected = [
        "weight_class", "f_1_name", "f_2_name", "winner", "result",
        "event_date", "event_name", "event_country", "finish_round", "finish_time",
    ]
    rename = {find(e): e for e in expected if find(e) and find(e) != e}
    rename = {k: v for k, v in rename.items() if k}
    if rename:
        df = df.rename(columns=rename)
    if "event_date" in df.columns:
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
        df["year"] = df["event_date"].dt.year
    else:
        df["year"] = pd.NA
    if "weight_class" not in df.columns:
        st.warning("Coluna 'weight_class' não encontrada no dataset; filtros por categoria ficarão desabilitados.")
        df["weight_class"] = pd.NA
    return df


if df.empty:
    st.error("Falha ao carregar os dados via Kaggle. Verifique o campo 'Dataset' e informe o nome do arquivo no campo 'Caminho do arquivo no dataset (opcional)'.")
    st.stop()

df = _normalize_columns(df)

# Mapeamento das categorias de peso (inglês -> português)
mapping_weight_class = dict([
    ("Flyweight","Mosca"),("Bantamweight","Galo"),("Featherweight","Pena"),
    ("Lightweight","Leve"),("Welterweight","Meio-médio"),("Middleweight","Médio"),
    ("Light Heavyweight","Meio-pesado"),("Heavyweight","Pesado"),("Strawweight","Palha"),
    ("Catch Weight","Peso combinado"),("Women's Bantamweight","Galo (Feminino)"),
    ("Women's Flyweight","Mosca (Feminino)"),("Women's Strawweight","Palha (Feminino)"),
    ("Women's Featherweight","Pena (Feminino)"),("Women's Lightweight","Leve (Feminino)")
])

# Coluna para exibição em PT; se não estiver no mapping, mantém o original
wc_series = df["weight_class"] if "weight_class" in df.columns else pd.Series(pd.NA, index=df.index)
df["weight_class_pt"] = wc_series.map(mapping_weight_class).fillna(wc_series)

# Inverso para converter seleções em PT de volta ao inglês para filtragem
pt_to_en = {v: k for k, v in mapping_weight_class.items()}

# ------------------------------------------------------------
# CABEÇALHO + FIGURA FIXA
# ------------------------------------------------------------
st.image("dashboard_capa.png", use_container_width=True)

st.title("🥊 UFC Fight Analytics")
st.caption(
    "Dashboard desenvolvido em Streamlit para explorar tendências históricas "
    "das lutas do UFC."
)

# ------------------------------------------------------------
# WIDGETS / FILTROS
# ------------------------------------------------------------
st.sidebar.header("🎛️ Filtros")

categorias = sorted(df["weight_class_pt"].dropna().unique().tolist())
categorias_selecionadas = st.sidebar.multiselect(
    "Categoria(s) de peso",
    options=categorias,
    default=categorias
)

ano_min = int(df["year"].dropna().min())
ano_max = int(df["year"].dropna().max())

periodo = st.sidebar.slider(
    "Período",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max)
)

resultados = sorted(df["result"].dropna().unique().tolist())
resultados_selecionados = st.sidebar.multiselect(
    "Resultado da luta",
    options=resultados,
    default=resultados
)

# ------------------------------------------------------------
# APLICAÇÃO DOS FILTROS
# ------------------------------------------------------------
df_filtrado = df[
    # Converte categorias selecionadas (PT) para os nomes originais (EN) antes de filtrar
    (df["weight_class"].isin([pt_to_en.get(c, c) for c in categorias_selecionadas])) &
    (df["year"].between(periodo[0], periodo[1])) &
    (df["result"].isin(resultados_selecionados))
].copy()

# ------------------------------------------------------------
# MÉTRICAS
# ------------------------------------------------------------
st.subheader("📌 Visão geral")

total_lutas = len(df_filtrado)
lutadores = set(df_filtrado["f_1_name"].dropna()) | set(df_filtrado["f_2_name"].dropna())
total_lutadores = len(lutadores)
total_ko = int(df_filtrado["result"].fillna("").str.contains("KO|TKO", regex=True).sum())
total_sub = int(df_filtrado["result"].fillna("").str.contains("Submission", case=False).sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lutas", f"{total_lutas:,}".replace(",", "."))
c2.metric("Lutadores", f"{total_lutadores:,}".replace(",", "."))
c3.metric("KO / TKO", f"{total_ko:,}".replace(",", "."))
c4.metric("Submissões", f"{total_sub:,}".replace(",", "."))

if df_filtrado.empty:
    st.warning("Nenhuma luta corresponde aos filtros selecionados.")
    st.stop()

# ------------------------------------------------------------
# GRÁFICO 1 - FORMAS DE RESULTADO
# ------------------------------------------------------------
st.subheader("📊 Distribuição dos resultados")

contagem_resultados = (
    df_filtrado["result"]
    .fillna("Não informado")
    .value_counts()
    .rename_axis("Resultado")
    .reset_index(name="Lutas")
)

fig_resultados = px.bar(
    contagem_resultados,
    x="Resultado",
    y="Lutas",
    text="Lutas",
    title="Quantidade de lutas por tipo de resultado"
)
fig_resultados.update_layout(
    xaxis_title="Resultado",
    yaxis_title="Número de lutas",
    xaxis_tickangle=-30
)
st.plotly_chart(fig_resultados, width='stretch')

# ------------------------------------------------------------
# GRÁFICO 2 - LUTADORES COM MAIS VITÓRIAS
# ------------------------------------------------------------
st.subheader("🏆 Lutadores com mais vitórias")

top_n = st.slider(
    "Quantidade de lutadores no ranking",
    min_value=5,
    max_value=25,
    value=10
)

vitorias = (
    df_filtrado["winner"]
    .dropna()
    .value_counts()
    .head(top_n)
    .rename_axis("Lutador")
    .reset_index(name="Vitórias")
    .sort_values("Vitórias", ascending=True)
)

fig_vitorias = px.bar(
    vitorias,
    x="Vitórias",
    y="Lutador",
    orientation="h",
    text="Vitórias",
    title=f"Top {top_n} lutadores por número de vitórias no recorte selecionado"
)
# Ajuste de layout para suportar muitos lutadores (evita que nomes sumaem)
fig_vitorias.update_layout(
    xaxis_title="Vitórias",
    yaxis_title="Lutador",
    height=max(300, 40 * top_n),
    margin=dict(l=250 if top_n >= 10 else 140, r=20, t=50, b=50)
)
# Garante que o Plotly ajuste margens automaticamente para rótulos longos
fig_vitorias.update_yaxes(automargin=True)
st.plotly_chart(fig_vitorias, width='stretch')

# ------------------------------------------------------------
# GRÁFICO 3 - LUTAS POR ANO
# ------------------------------------------------------------
st.subheader("📈 Evolução do número de lutas")

lutas_ano = (
    df_filtrado.dropna(subset=["year"])
    .groupby("year")
    .size()
    .reset_index(name="Lutas")
)

fig_ano = px.line(
    lutas_ano,
    x="year",
    y="Lutas",
    markers=True,
    title="Número de lutas por ano"
)
fig_ano.update_layout(
    xaxis_title="Ano",
    yaxis_title="Número de lutas"
)
st.plotly_chart(fig_ano, width='stretch')

# ------------------------------------------------------------
# ANÁLISE INDIVIDUAL DE LUTADOR
# ------------------------------------------------------------
st.divider()
st.subheader("🔎 Análise individual de lutador")

nomes_lutadores = sorted(lutadores)
lutador = st.selectbox(
    "Selecione um lutador",
    options=nomes_lutadores
)

lutas_lutador = df_filtrado[
    (df_filtrado["f_1_name"] == lutador) |
    (df_filtrado["f_2_name"] == lutador)
].copy()

vitorias_lutador = int((lutas_lutador["winner"] == lutador).sum())
derrotas_lutador = int(
    lutas_lutador["winner"].notna().sum() - vitorias_lutador
)

a1, a2, a3 = st.columns(3)
a1.metric("Lutas no recorte", len(lutas_lutador))
a2.metric("Vitórias", vitorias_lutador)
a3.metric("Outros resultados / derrotas", derrotas_lutador)

# Consolidação das estatísticas, independentemente de o atleta estar como f_1 ou f_2
estatisticas = []
for _, luta in lutas_lutador.iterrows():
    if luta["f_1_name"] == lutador:
        estatisticas.append({
            "Golpes significativos": luta.get("f_1_sig_strikes_succ", 0),
            "Takedowns": luta.get("f_1_takedown_succ", 0),
            "Knockdowns": luta.get("f_1_knockdowns", 0),
        })
    else:
        estatisticas.append({
            "Golpes significativos": luta.get("f_2_sig_strikes_succ", 0),
            "Takedowns": luta.get("f_2_takedown_succ", 0),
            "Knockdowns": luta.get("f_2_knockdowns", 0),
        })

estat_df = pd.DataFrame(estatisticas).apply(pd.to_numeric, errors="coerce").fillna(0)

if not estat_df.empty:
    totais = estat_df.sum().reset_index()
    totais.columns = ["Estatística", "Total"]

    fig_lutador = px.bar(
        totais,
        x="Estatística",
        y="Total",
        text="Total",
        title=f"Estatísticas acumuladas de {lutador} no recorte"
    )
    st.plotly_chart(fig_lutador, width='stretch')

    # Opção para exibir as lutas que compõem as estatísticas do lutador
    with st.expander(f"Ver lutas usadas para as estatísticas de {lutador}"):
        cols_lutas = [
            "event_date",
            "event_name",
            "weight_class",
            "f_1_name",
            "f_2_name",
            "winner",
            "result",
            "finish_round",
            "finish_time",
            "event_country"
        ]
        lutas_display = lutas_lutador[cols_lutas].copy()
        # Determina o oponente do lutador na linha
        lutas_display["Oponente"] = lutas_display.apply(
            lambda r: r["f_2_name"] if r["f_1_name"] == lutador else r["f_1_name"],
            axis=1
        )
        # Traduz a categoria para português para exibição
        lutas_display["weight_class"] = lutas_display["weight_class"].map(mapping_weight_class).fillna(lutas_display["weight_class"])

        lutas_display = lutas_display.rename(columns={
            "event_date": "Data",
            "event_name": "Evento",
            "weight_class": "Categoria",
            "f_1_name": "Lutador 1",
            "f_2_name": "Lutador 2",
            "winner": "Vencedor",
            "result": "Resultado",
            "finish_round": "Round final",
            "finish_time": "Tempo",
            "event_country": "País"
        })
        # Reordena para mostrar primeiro a data, oponente e demais campos
        display_cols = ["Data", "Evento", "Categoria", "Oponente", "Vencedor", "Resultado", "Round final", "Tempo", "País"]
        st.dataframe(lutas_display[display_cols], width='stretch', hide_index=True)

# ------------------------------------------------------------
# TABELA DOS DADOS FILTRADOS
# ------------------------------------------------------------
with st.expander("📋 Ver dados filtrados"):
    colunas_tabela = [
        "event_date",
        "event_name",
        "weight_class",
        "f_1_name",
        "f_2_name",
        "winner",
        "result",
        "finish_round",
        "finish_time",
        "event_country"
    ]
    tabela = df_filtrado[colunas_tabela].copy()
    # Mostra a categoria de peso em português na tabela
    tabela["weight_class"] = tabela["weight_class"].map(mapping_weight_class).fillna(tabela["weight_class"])
    tabela = tabela.rename(columns={
        "event_date": "Data",
        "event_name": "Evento",
        "weight_class": "Categoria",
        "f_1_name": "Lutador 1",
        "f_2_name": "Lutador 2",
        "winner": "Vencedor",
        "result": "Resultado",
        "finish_round": "Round final",
        "finish_time": "Tempo",
        "event_country": "País"
    })
    st.dataframe(tabela, width='stretch', hide_index=True)

# ------------------------------------------------------------
# RODAPÉ
# ------------------------------------------------------------
st.divider()
st.caption(
    "Projeto acadêmico desenvolvido com Python, Pandas, Streamlit e Plotly."
)
