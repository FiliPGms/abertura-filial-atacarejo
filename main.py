import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Análise de Viabilidade de Expansão",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)


def format_brl(value):
    """Formata valor para o padrão moeda brasileiro."""
    if pd.isna(value):
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def classificar_viabilidade(row):
    """Aplica regra condicional para classificação de viabilidade."""
    if row['payback_meses'] <= 38 and row['qtd_concorrentes_diretos'] <= 5:
        return "Viável"
    elif row['payback_meses'] > 45 or row['custo_m2_aluguel'] >= 90.00:
        return "Inviável"
    else:
        return "Parcialmente Viável"

def carregar_dados():
  
    df = pd.read_csv("dados.txt")
    
    df['receita_anual_estimada'] = df['faturamento_bruto_mensal'] * 12
    df['custo_variavel_estimado'] = df['faturamento_bruto_mensal'] * 0.80
    df['custo_fixo_estimado'] = df['faturamento_bruto_mensal'] * 0.05
    df['lucro_liquido_mensal'] = df['faturamento_bruto_mensal'] - df['custo_variavel_estimado'] - df['custo_fixo_estimado']
    
    df['ponto_de_equilibrio_mensal'] = df['custo_fixo_estimado'] / (1 - (df['custo_variavel_estimado'] / df['faturamento_bruto_mensal']))
    
    df['investimento_inicial'] = df['investimento_inicial_milhoes'] * 1000000
    df['payback_meses'] = df['investimento_inicial'] / df['lucro_liquido_mensal']
    
    df['viabilidade'] = df.apply(classificar_viabilidade, axis=1)
    
    df['faturamento_formatado'] = df['faturamento_bruto_mensal'].apply(format_brl)
    df['investimento_formatado'] = df['investimento_inicial'].apply(format_brl)
    df['renda_formatada'] = df['renda_media_mensal'].apply(format_brl)
    df['custo_aluguel_formatado'] = df['custo_m2_aluguel'].apply(format_brl)

    return df

df = carregar_dados()

#streamlit aqui

st.title("Análise de Viabilidade de Expansão - Atacarejo (São Luís - MA)")
st.markdown("""
- **Ramo:** Varejo Alimentar e Atacarejo.
- **Empresa-Modelo:** Grupo Mateus / Mix Mateus.
- **Público-Alvo:** Famílias (consumo essencial mensal), pequenos comerciantes, lanchonetes e transformadores que buscam preço competitivo e grandes volumes.
""")

st.sidebar.header("Filtros de Análise")
bairros = ["Todos"] + list(df['bairro'].unique())
selected_bairro = st.sidebar.selectbox("Selecione o Bairro", bairros)

if selected_bairro != "Todos":
    df_filtered = df[df['bairro'] == selected_bairro].copy()
else:
    df_filtered = df.copy()

st.markdown("### Indicadores Financeiros Globais")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(label="Investimento Inicial Médio", value=format_brl(df_filtered['investimento_inicial'].mean()))
with kpi2:
    st.metric(label="Receita Anual Est. Média", value=format_brl(df_filtered['receita_anual_estimada'].mean()))
with kpi3:
    st.metric(label="Ponto de Equilíbrio Mensal", value=format_brl(df_filtered['ponto_de_equilibrio_mensal'].mean()))
with kpi4:
    st.metric(label="Ticket Médio", value=format_brl(df_filtered['ticket_medio_estimado'].mean()))
with kpi5:
    st.metric(label="Payback Médio (Meses)", value=f"{df_filtered['payback_meses'].mean():.1f}")

st.divider()


st.markdown("### Gráficos Analíticos")


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

st.markdown("### Diagnóstico Estratégico e Setorial")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Vantagens:**\n- Consumo essencial/recorrente\n- Alto volume de vendas\n- Operação multicanal")
with c2:
    st.markdown("**Desvantagens:**\n- Alto investimento inicial\n- Margem de lucro espremida\n- Alto custo de segurança e perdas")
with c3:
    st.markdown("**Barreiras de Entrada:**\n- Concorrência consolidada localmente\n- Custo logístico para abastecer a ilha\n- Necessidade de grandes áreas físicas (terrenos escassos)")

with st.expander("Análise Setorial: 5 Forças de Porter", expanded=False):
    st.markdown("""
    - **Rivalidade entre concorrentes (Altíssima):** Disputa de preços com líderes regionais e nacionais.
    - **Poder de barganha dos clientes (Alta):** Sensibilidade a preço no atacarejo.
    - **Poder de barganha dos fornecedores (Média):** Dependência de grandes indústrias, equilibrada pelo volume.
    - **Ameaça de novos entrantes (Baixa):** Alta barreira de capital e custo logístico de ilha.
    - **Ameaça de substitutos (Baixa):** Alimento é essencial; substituição ocorre apenas de canal/mercadinho.
    """)

st.divider()

st.markdown("### Decisão, Localização e Recomendação Final")

#dataframe exibido
cols_exibicao = [
    'bairro', 'zona', 'viabilidade', 
    'investimento_inicial', 'receita_anual_estimada', 'ponto_de_equilibrio_mensal',
    'payback_meses', 'qtd_concorrentes_diretos', 'distancia_cd_km', 'fluxo_veiculos'
]

df_view = df_filtered[cols_exibicao].copy()

df_view['investimento_inicial'] = df_view['investimento_inicial'].apply(format_brl)
df_view['receita_anual_estimada'] = df_view['receita_anual_estimada'].apply(format_brl)
df_view['ponto_de_equilibrio_mensal'] = df_view['ponto_de_equilibrio_mensal'].apply(format_brl)
df_view['payback_meses'] = df_view['payback_meses'].round(1)

df_view.rename(columns={
    'bairro': 'Bairro', 'zona': 'Zona', 'viabilidade': 'Viabilidade',
    'investimento_inicial': 'Investimento', 'receita_anual_estimada': 'Receita Anual (Est)',
    'ponto_de_equilibrio_mensal': 'Ponto Equilíbrio (Mês)', 'payback_meses': 'Payback (Meses)',
    'qtd_concorrentes_diretos': 'Concorrentes', 'distancia_cd_km': 'Distância CD (km)',
    'fluxo_veiculos': 'Fluxo Veículos'
}, inplace=True)

st.dataframe(df_view, width='stretch', hide_index=True)

if selected_bairro != "Todos":
    bairro_data = df_filtered.iloc[0]
    viabilidade = bairro_data['viabilidade']
    
    st.markdown(f"#### Parecer para: **{selected_bairro}**")
    
    if viabilidade == "Viável":
        st.success(f"**Recomendação: Expansão APROVADA para {selected_bairro}.**\n\nJustificativa: Equilíbrio entre custo logístico reduzido e concorrência administrável, gerando retorno sobre investimento dentro de parâmetros aceitáveis.")
    elif viabilidade == "Parcialmente Viável":
        st.warning(f"**Recomendação: Atenção.**\n\nViabilidade parcial em {selected_bairro}. Exige análise profunda de viabilidade e mitigação de riscos devido a payback longo ou alta concorrência.")
    else:
        st.error(f"**Recomendação: Expansão REJEITADA para {selected_bairro}.**\n\nCondições de mercado atuais não sustentam os investimentos necessários sem risco crítico.")
        
    if selected_bairro in ["Sao Cristovao", "Centro"]:
        st.info("💡 **Localização Estratégica Recomendada:** Pelos critérios do edital, esta localização apresenta vantagens estratégicas significativas em relação à média geral da ilha.")
