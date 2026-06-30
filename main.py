import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Análise de Viabilidade de Expansão",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funções utilitárias
def format_brl(value):
    """Formata valor para o padrão moeda brasileiro."""
    if pd.isna(value):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def classificar_viabilidade(row):
    """Aplica regra condicional para classificação de viabilidade."""
    if row['payback_meses'] <= 45 and row['qtd_concorrentes_diretos'] <= 5:
        return "Viável"
    elif 46 <= row['payback_meses'] <= 60 or row['fluxo_veiculos'] == "Alto":
        return "Parcialmente Viável"
    else:
        return "Inviável"

@st.cache_data
def carregar_dados():
    # 1. FONTE DE DADOS
    df = pd.read_csv("dados.txt")
    
    # 2. REGRAS DE NEGÓCIO E CÁLCULOS FINANCEIROS
    # lucro_liquido_estimado: margem de 15%
    df['lucro_liquido_estimado'] = df['faturamento_bruto_mensal'] * 0.15
    
    # payback_meses: (investimento * 1.000.000) / lucro
    df['investimento_inicial'] = df['investimento_inicial_milhoes'] * 1000000
    df['payback_meses'] = df['investimento_inicial'] / df['lucro_liquido_estimado']
    
    # classificacao_viabilidade
    df['classificacao_viabilidade'] = df.apply(classificar_viabilidade, axis=1)
    
    # Colunas formatadas para tooltip
    df['faturamento_formatado'] = df['faturamento_bruto_mensal'].apply(format_brl)
    df['investimento_formatado'] = df['investimento_inicial'].apply(format_brl)
    df['renda_formatada'] = df['renda_media_mensal'].apply(format_brl)
    df['custo_aluguel_formatado'] = df['custo_m2_aluguel'].apply(format_brl)
    df['lucro_formatado'] = df['lucro_liquido_estimado'].apply(format_brl)
    df['ticket_formatado'] = df['ticket_medio_estimado'].apply(format_brl)

    return df

df = carregar_dados()

# 3. ESTRUTURA E DESIGN DO DASHBOARD (STREAMLIT)
# A. Cabeçalho e Contextualização
st.title("Análise de Viabilidade de Expansão - Atacarejo (São Luís - MA)")
st.markdown("""
**Foco Estratégico:** Avaliação de novos pontos comerciais para a implementação de unidades voltadas 
ao consumo das famílias maranhenses, priorizando alto volume de vendas e eficiência na logística de abastecimento.
""")

# Filtro lateral
st.sidebar.header("Filtros de Análise")
zonas = ["Todas"] + list(df['zona'].unique())
selected_zona = st.sidebar.selectbox("Selecione a Zona", zonas)

df_filtered = df.copy()
if selected_zona != "Todas":
    df_filtered = df_filtered[df_filtered['zona'] == selected_zona]

bairros = ["Todos"] + list(df_filtered['bairro'].unique())
selected_bairro = st.sidebar.selectbox("Selecione o Bairro", bairros)

if selected_bairro != "Todos":
    df_filtered = df_filtered[df_filtered['bairro'] == selected_bairro]

# B. Cartões de Indicadores (KPI Cards)
st.markdown("### Indicadores Chave de Desempenho")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    fat_medio = df_filtered['faturamento_bruto_mensal'].mean()
    st.metric(label="Faturamento Bruto Médio (Proj)", value=format_brl(fat_medio))

with kpi2:
    ticket_medio = df_filtered['ticket_medio_estimado'].mean()
    st.metric(label="Ticket Médio", value=format_brl(ticket_medio))

with kpi3:
    inv_medio = df_filtered['investimento_inicial_milhoes'].mean()
    st.metric(label="Investimento Inicial Médio", value=f"R$ {inv_medio:,.1f} Milhões".replace(".", ","))

with kpi4:
    payback_medio = df_filtered['payback_meses'].mean()
    st.metric(label="Payback Médio (Meses)", value=f"{payback_medio:.1f}")

st.divider()

# C. Gráficos Interativos (Plotly Express)
st.markdown("### Análise de Mercado e Potencial")

# Gráfico 1: Faturamento Bruto vs. Investimento Inicial por Bairro
df_g1 = df_filtered.sort_values(by="faturamento_bruto_mensal", ascending=False)
fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=df_g1['bairro'],
    y=df_g1['faturamento_bruto_mensal'],
    name='Faturamento Bruto',
    marker_color='#1f77b4',
    customdata=df_g1['faturamento_formatado'],
    hovertemplate="<b>%{x}</b><br>Faturamento: %{customdata}<extra></extra>"
))
fig1.add_trace(go.Bar(
    x=df_g1['bairro'],
    y=df_g1['investimento_inicial'],
    name='Investimento Inicial',
    marker_color='#ff7f0e',
    customdata=df_g1['investimento_formatado'],
    hovertemplate="<b>%{x}</b><br>Investimento: %{customdata}<extra></extra>"
))
fig1.update_layout(
    title="Faturamento Bruto vs. Investimento Inicial por Bairro",
    barmode='group',
    xaxis_title="Bairro",
    yaxis_title="Valor (R$)",
    legend_title="Indicador",
    hovermode="x unified"
)
st.plotly_chart(fig1, width='stretch')

col_graf2, col_graf3 = st.columns(2)

with col_graf2:
    # Gráfico 2: Renda vs População (Bolhas)
    fig2 = px.scatter(
        df_filtered, 
        x="renda_media_mensal", 
        y="populacao_estimada", 
        size="qtd_concorrentes_diretos", 
        color="zona",
        hover_name="bairro",
        custom_data=['renda_formatada', 'qtd_concorrentes_diretos'],
        labels={
            "renda_media_mensal": "Renda Média Mensal (R$)",
            "populacao_estimada": "População Estimada",
            "zona": "Zona"
        },
        title="Renda vs População (Tamanho = Concorrência)",
        size_max=30
    )
    fig2.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Renda: %{customdata[0]}<br>População: %{y}<br>Concorrentes: %{customdata[1]}<extra></extra>"
    )
    st.plotly_chart(fig2, width='stretch')

with col_graf3:
    # Gráfico 3: Custo do M² de Aluguel
    df_g3 = df_filtered.sort_values(by="custo_m2_aluguel", ascending=True)
    fig3 = px.bar(
        df_g3,
        x="custo_m2_aluguel",
        y="bairro",
        orientation='h',
        custom_data=['custo_aluguel_formatado'],
        labels={
            "custo_m2_aluguel": "Custo M² (R$)",
            "bairro": ""
        },
        title="Custo do M² de Aluguel por Bairro",
        color="custo_m2_aluguel",
        color_continuous_scale="Reds"
    )
    fig3.update_traces(
        hovertemplate="<b>%{y}</b><br>Custo M²: %{customdata[0]}<extra></extra>"
    )
    st.plotly_chart(fig3, width='stretch')

st.divider()

# D. Análise Estratégica: As 5 Forças de Porter
st.markdown("### Análise Estratégica Setorial: 5 Forças de Porter (São Luís)")
with st.expander("Ver Análise Completa", expanded=False):
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.info("**1. Rivalidade entre concorrentes (Altíssima)**\n\nDisputa de preços acirrada com líderes regionais e nacionais.")
    col_p2.warning("**2. Poder de barganha dos clientes (Alto)**\n\nAlta sensibilidade a preço no segmento de atacarejo.")
    col_p3.success("**3. Poder de barganha dos fornecedores (Médio)**\n\nDependência de grandes indústrias, porém equilibrada pelo volume de compra.")
    
    col_p4, col_p5 = st.columns(2)
    col_p4.success("**4. Ameaça de novos entrantes (Baixa/Média)**\n\nAlta barreira de capital e elevado custo logístico de entrada em ilha.")
    col_p5.success("**5. Ameaça de substitutos (Baixa)**\n\nAlimento é item essencial; substituição ocorre apenas de canal ou pequenos mercadinhos.")

st.divider()

# E. Matriz de Tomada de Decisão e Recomendação Final
st.markdown("### Matriz de Decisão e Dados Detalhados")

# Prepara DataFrame para exibição
cols_exibicao = [
    'bairro', 'zona', 'classificacao_viabilidade', 
    'faturamento_formatado', 'investimento_formatado', 'lucro_formatado',
    'payback_meses', 'qtd_concorrentes_diretos', 'distancia_cd_km', 'fluxo_veiculos'
]

df_view = df_filtered[cols_exibicao].copy()
df_view.rename(columns={
    'bairro': 'Bairro', 'zona': 'Zona', 'classificacao_viabilidade': 'Viabilidade',
    'faturamento_formatado': 'Faturamento (Proj)', 'investimento_formatado': 'Investimento',
    'lucro_formatado': 'Lucro (Proj)', 'payback_meses': 'Payback (Meses)',
    'qtd_concorrentes_diretos': 'Concorrentes', 'distancia_cd_km': 'Distância CD (km)',
    'fluxo_veiculos': 'Fluxo Veículos'
}, inplace=True)

# Arredonda colunas numéricas
df_view['Payback (Meses)'] = df_view['Payback (Meses)'].round(1)

st.dataframe(df_view, width='stretch', hide_index=True)

# Recomendação Final se um bairro específico for selecionado
if selected_bairro != "Todos":
    st.markdown(f"#### Recomendação Final para: **{selected_bairro}**")
    bairro_data = df_filtered.iloc[0]
    viabilidade = bairro_data['classificacao_viabilidade']
    
    justificativa = (
        f"Payback estimado em {bairro_data['payback_meses']:.1f} meses, "
        f"com {bairro_data['qtd_concorrentes_diretos']} concorrente(s) direto(s) "
        f"e distância de {bairro_data['distancia_cd_km']} km do Centro de Distribuição."
    )
    
    if viabilidade == "Viável":
        st.success(f"**Veredito: {viabilidade}**\n\nO bairro apresenta excelentes indicadores para expansão. {justificativa}")
    elif viabilidade == "Parcialmente Viável":
        st.warning(f"**Veredito: {viabilidade}**\n\nOportunidade moderada. Exige análise cuidadosa dos riscos associados. {justificativa}")
    else:
        st.error(f"**Veredito: {viabilidade}**\n\nBairro não recomendado para a estratégia atual devido a indicadores fora da margem de segurança. {justificativa}")
