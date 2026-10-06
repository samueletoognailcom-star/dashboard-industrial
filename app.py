import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="Dashboard Industrial",
    page_icon="⚙️",
    layout="wide"
)

# =========================
# LIMITES DA CURVA ABC
# =========================
LIMITE_A = 100_000
LIMITE_B = 110_000
LIMITE_C = 115_000


# =========================
# CLASSIFICAÇÃO ABC
# =========================
def classificar_tonelagem(tonelagem):
    if tonelagem <= LIMITE_A:
        return "A", "SEGURO", "🟢"
    elif tonelagem <= LIMITE_B:
        return "B", "ALERTA", "🟡"
    elif tonelagem < LIMITE_C:
        return "C", "CRÍTICO", "🔴"
    else:
        return "TROCA", "PRONTO PARA TROCA", "🚨"


# =========================
# ESTADOS DE OPERAÇÃO
# =========================
def estado_operacao(estado):
    estados = {
        1: ("PRODUZINDO", "🟢"),
        2: ("STAND-BY", "🟡"),
        3: ("FORA DO CENTRO DE USINAGEM", "🔴")
    }

    return estados.get(estado, ("DESCONHECIDO", "⚪"))


# =========================
# GERAÇÃO DE DADOS
# =========================
def gerar_dados_historicos():

    agora = datetime.now()

    registros = []

    tonelagem = 94_000

    for i in range(24):

        horario = agora - timedelta(
            minutes=(23 - i) * 30
        )

        tonelagem += random.randint(100, 700)

        if i in [5, 6]:
            estado = 2

        elif i == 18:
            estado = 3

        else:
            estado = 1

        classe, situacao, icone = classificar_tonelagem(
            tonelagem
        )

        registros.append({

            "Data": horario.strftime("%d/%m/%Y"),

            "Hora": horario.strftime("%H:%M"),

            "DataHora": horario,

            "Tonelagem": tonelagem,

            "Classe": classe,

            "Situação": situacao,

            "Estado": estado,

            "Estado Nome": estado_operacao(estado)[0]

        })

    return pd.DataFrame(registros)


# =========================
# GRÁFICO
# =========================
def criar_grafico(df):

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=df["DataHora"],

            y=df["Tonelagem"],

            mode="lines+markers",

            name="Tonelagem",

            line=dict(width=3),

            marker=dict(size=7)

        )

    )

    fig.add_hline(

        y=LIMITE_A,

        line_dash="dash",

        annotation_text="100.000 t - Limite A"

    )

    fig.add_hline(

        y=LIMITE_B,

        line_dash="dash",

        annotation_text="110.000 t - Limite B"

    )

    fig.add_hline(

        y=LIMITE_C,

        line_dash="dash",

        annotation_text="115.000 t - TROCA"

    )

    fig.update_layout(

        title="Evolução da Tonelagem",

        xaxis_title="Horário",

        yaxis_title="Tonelagem (t)",

        height=450,

        hovermode="x unified"

    )

    return fig


# =========================
# INICIALIZAÇÃO
# =========================
if "dados" not in st.session_state:

    st.session_state.dados = gerar_dados_historicos()


df = st.session_state.dados


# =========================
# ÚLTIMA LEITURA
# =========================
ultima_linha = df.iloc[-1]

tonelagem_atual = float(
    ultima_linha["Tonelagem"]
)

classe, situacao, icone = classificar_tonelagem(
    tonelagem_atual
)

estado_atual = int(
    ultima_linha["Estado"]
)

nome_estado, icone_estado = estado_operacao(
    estado_atual
)

ultima_atualizacao = ultima_linha["DataHora"]


# =========================
# MENU LATERAL
# =========================
with st.sidebar:

    st.title("⚙️ CONTROLE")

    st.markdown("---")

    st.subheader("Curva ABC")

    st.write("🟢 A — Seguro")

    st.write("🟡 B — Alerta")

    st.write("🔴 C — Crítico")

    st.write("🚨 ≥ 115.000 t — Troca")

    st.markdown("---")

    st.subheader("Estados")

    st.write("🟢 1 — Produzindo")

    st.write("🟡 2 — Stand-by")

    st.write("🔴 3 — Fora do centro")

    st.markdown("---")

    if st.button("🔄 Simular nova leitura"):

        ultima_tonelagem = float(
            st.session_state.dados.iloc[-1]["Tonelagem"]
        )

        novo_valor = (
            ultima_tonelagem
            + random.randint(100, 700)
        )

        novo_estado = random.choice(
            [1, 1, 1, 2, 3]
        )

        agora = datetime.now()

        nova_classe, nova_situacao, novo_icone = (
            classificar_tonelagem(novo_valor)
        )

        nova_linha = pd.DataFrame([{

            "Data": agora.strftime("%d/%m/%Y"),

            "Hora": agora.strftime("%H:%M"),

            "DataHora": agora,

            "Tonelagem": novo_valor,

            "Classe": nova_classe,

            "Situação": nova_situacao,

            "Estado": novo_estado,

            "Estado Nome": estado_operacao(
                novo_estado
            )[0]

        }])

        st.session_state.dados = pd.concat(

            [
                st.session_state.dados,
                nova_linha
            ],

            ignore_index=True

        )

        st.rerun()


# =========================
# TÍTULO
# =========================
st.title("⚙️ Dashboard Industrial")

st.caption(
    "Monitoramento de tonelagem, "
    "classificação ABC e estado de operação"
)

st.markdown("---")


# =========================
# ALERTAS
# =========================
if tonelagem_atual >= LIMITE_C:

    st.error(
        f"🚨 CILINDRO PRONTO PARA TROCA — "
        f"Tonelagem atual: {tonelagem_atual:,.0f} t"
    )

elif tonelagem_atual > LIMITE_B:

    st.warning(
        "⚠️ ATENÇÃO: Cilindro em nível crítico."
    )

elif tonelagem_atual > LIMITE_A:

    st.warning(
        "⚠️ ATENÇÃO: Cilindro entrou na faixa de alerta."
    )

else:

    st.success(
        "✅ Cilindro operando dentro da faixa segura."
    )


# =========================
# INDICADORES
# =========================
col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(

        "Tonelagem Atual",

        f"{tonelagem_atual:,.0f} t"

    )


with col2:

    st.metric(

        "Classificação ABC",

        f"{icone} {classe}"

    )


with col3:

    st.metric(

        "Situação",

        situacao

    )


with col4:

    st.metric(

        "Estado",

        f"{icone_estado} {estado_atual}"

    )


# =========================
# ESTADO DE OPERAÇÃO
# =========================
st.markdown("---")

st.subheader("⚙️ Estado de Operação")


col1, col2, col3 = st.columns(3)


with col1:

    if estado_atual == 1:

        st.success(
            "🟢 ESTADO 1\n\nPRODUZINDO"
        )

    else:

        st.info(
            "Estado 1\n\nProduzindo"
        )


with col2:

    if estado_atual == 2:

        st.warning(
            "🟡 ESTADO 2\n\nSTAND-BY"
        )

    else:

        st.info(
            "Estado 2\n\nStand-by"
        )


with col3:

    if estado_atual == 3:

        st.error(
            "🔴 ESTADO 3\n\n"
            "FORA DO CENTRO DE USINAGEM"
        )

    else:

        st.info(
            "Estado 3\n\n"
            "Fora do centro"
        )


# =========================
# NÍVEL DE TONELAGEM
# =========================
st.markdown("---")

st.subheader("📊 Nível de Tonelagem")


porcentagem = min(

    tonelagem_atual / LIMITE_C,

    1.0

)


st.progress(porcentagem)


st.write(

    f"**{tonelagem_atual:,.0f} t** "
    f"de **{LIMITE_C:,.0f} t**"

)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.write("🟢 **A — Seguro**")

    st.write("Até 100.000 t")


with col2:

    st.write("🟡 **B — Alerta**")

    st.write("100.001 – 110.000 t")


with col3:

    st.write("🔴 **C — Crítico**")

    st.write("110.001 – 114.999 t")


with col4:

    st.write("🚨 **Troca**")

    st.write("≥ 115.000 t")


# =========================
# GRÁFICO
# =========================
st.markdown("---")

st.subheader("📈 Evolução da Tonelagem")


fig = criar_grafico(df)


st.plotly_chart(

    fig,

    use_container_width=True

)


# =========================
# HISTÓRICO
# =========================
st.markdown("---")

st.subheader("📋 Histórico de Operação")


df_exibicao = df.copy()


df_exibicao["Tonelagem"] = (

    df_exibicao["Tonelagem"]

    .apply(
        lambda x: f"{x:,.0f} t"
    )

)


df_exibicao = df_exibicao[

    [
        "Data",
        "Hora",
        "Tonelagem",
        "Classe",
        "Situação",
        "Estado",
        "Estado Nome"
    ]

]


st.dataframe(

    df_exibicao,

    use_container_width=True,

    hide_index=True

)


# =========================
# ATUALIZAÇÃO
# =========================
st.markdown("---")


st.info(

    f"🕒 Última atualização: "
    f"{ultima_atualizacao.strftime('%d/%m/%Y às %H:%M')}"

)


# =========================
# EXPORTAÇÃO
# =========================
st.subheader("📥 Exportação")


csv = df.to_csv(

    index=False

).encode("utf-8")


st.download_button(

    label="📥 Baixar histórico em CSV",

    data=csv,

    file_name="historico_dashboard.csv",

    mime="text/csv"

)


st.markdown("---")


st.caption(

    "Dashboard Industrial • "
    "Python + Streamlit • "
    "Modo de simulação — sem conexão com CLP"

)
