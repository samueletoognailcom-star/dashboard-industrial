import random
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Dashboard Industrial", page_icon="⚙️", layout="wide"
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
        return "TROCA", "PRONTO PARA TROCA / ARMAZENAMENTO", "🚨"


# =========================
# ESTADOS DE OPERAÇÃO
# =========================
def estado_operacao(estado):
    estados = {
        1: ("PRODUZINDO", "🟢"),
        2: ("STAND-BY", "🟡"),
        3: ("FORA DO CENTRO DE USINAGEM", "🔴"),
        4: ("NO ARMAZENAMENTO / TROCADO", "📦"),
    }
    return estados.get(estado, ("DESCONHECIDO", "⚪"))


# =========================
# GERAÇÃO DE DADOS INICIAIS
# =========================
def gerar_dados_historicos():
    agora = datetime.now()
    registros = []
    tonelagem = 94_000

    for i in range(24):
        horario = agora - timedelta(minutes=(23 - i) * 30)
        tonelagem += random.randint(100, 700)

        if i in [5, 6]:
            estado = 2
        elif i == 18:
            estado = 3
        else:
            estado = 1

        classe, situacao, icone = classificar_tonelagem(tonelagem)

        registros.append(
            {
                "Data": horario.strftime("%d/%m/%Y"),
                "Hora": horario.strftime("%H:%M"),
                "DataHora": horario,
                "Tonelagem": tonelagem,
                "Classe": classe,
                "Situação": situacao,
                "Estado": estado,
                "Estado Nome": estado_operacao(estado)[0],
            }
        )

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
            marker=dict(size=7),
        )
    )

    fig.add_hline(
        y=LIMITE_A, line_dash="dash", annotation_text="100.000 t - Limite A"
    )
    fig.add_hline(
        y=LIMITE_B, line_dash="dash", annotation_text="110.000 t - Limite B"
    )
    fig.add_hline(
        y=LIMITE_C, line_dash="dash", annotation_text="115.000 t - TROCA"
    )

    fig.update_layout(
        title="Evolução da Tonelagem",
        xaxis_title="Horário",
        yaxis_title="Tonelagem (t)",
        height=450,
        hovermode="x unified",
    )

    return fig


# =========================
# INICIALIZAÇÃO DE ESTADO
# =========================
if "dados" not in st.session_state:
    st.session_state.dados = gerar_dados_historicos()

if "diametro_cilindro" not in st.session_state:
    st.session_state.diametro_cilindro = 500.0  # Valor padrão em mm

df = st.session_state.dados


# =========================
# ÚLTIMA LEITURA
# =========================
ultima_linha = df.iloc[-1]
tonelagem_atual = float(ultima_linha["Tonelagem"])
classe, situacao, icone = classificar_tonelagem(tonelagem_atual)
estado_atual = int(ultima_linha["Estado"])
nome_estado, icone_estado = estado_operacao(estado_atual)
ultima_atualizacao = ultima_linha["DataHora"]


# =========================
# MENU LATERAL - OPERADOR E TROCA
# =========================
with st.sidebar:
    st.title("⚙️ PAINEL DO OPERADOR")
    st.markdown("---")

    # Informação do diâmetro atual
    st.subheader("📏 Diâmetro Atual")
    st.info(f"**{st.session_state.diametro_cilindro:.2f} mm**")

    st.markdown("---")
    st.subheader("🚨 Ação do Operador (Troca)")

    # Entrada do novo diâmetro do cilindro
    novo_diametro_input = st.number_input(
        "Novo Diâmetro do Cilindro (mm):",
        min_value=100.0,
        max_value=2000.0,
        value=float(st.session_state.diametro_cilindro),
        step=0.5,
    )

    # Botão de confirmação de troca
    if st.button("🚨 AVISAR TROCA / ENVIAR PARA ARMAZENAMENTO"):
        agora = datetime.now()

        # Atualiza o diâmetro na sessão
        st.session_state.diametro_cilindro = novo_diametro_input

        # Cria nova linha resetando a tonelagem e marcando Estado 4 (Armazenamento)
        nova_linha = pd.DataFrame(
            [
                {
                    "Data": agora.strftime("%d/%m/%Y"),
                    "Hora": agora.strftime("%H:%M"),
                    "DataHora": agora,
                    "Tonelagem": 0,  # Reseta a tonelagem para o novo cilindro
                    "Classe": "A",
                    "Situação": "NO ARMAZENAMENTO",
                    "Estado": 4,
                    "Estado Nome": estado_operacao(4)[0],
                }
            ]
        )

        st.session_state.dados = pd.concat(
            [st.session_state.dados, nova_linha], ignore_index=True
        )

        st.success("Troca registrada! Cilindro enviado para o Armazenamento.")
        st.rerun()

    st.markdown("---")
    st.subheader("Simulação")

    if st.button("🔄 Simular nova leitura"):
        ultima_tonelagem = float(
            st.session_state.dados.iloc[-1]["Tonelagem"]
        )
        novo_valor = ultima_tonelagem + random.randint(100, 700)
        novo_estado = random.choice([1, 1, 1, 2, 3])
        agora = datetime.now()

        nova_classe, nova_situacao, novo_icone = classificar_tonelagem(
            novo_valor
        )

        nova_linha = pd.DataFrame(
            [
                {
                    "Data": agora.strftime("%d/%m/%Y"),
                    "Hora": agora.strftime("%H:%M"),
                    "DataHora": agora,
                    "Tonelagem": novo_valor,
                    "Classe": nova_classe,
                    "Situação": nova_situacao,
                    "Estado": novo_estado,
                    "Estado Nome": estado_operacao(novo_estado)[0],
                }
            ]
        )

        st.session_state.dados = pd.concat(
            [st.session_state.dados, nova_linha], ignore_index=True
        )

        st.rerun()


# =========================
# TÍTULO E PAINEL
# =========================
st.title("⚙️ Dashboard Industrial - Monitoramento de Tonelagem")
st.caption("Controle e registro de trocas de cilindros")

st.markdown("---")


# =========================
# ALERTAS E MENSAGENS DE TROCA
# =========================
if estado_atual == 4:
    st.info(
        f"📦 **CILINDRO NO ARMAZENAMENTO** — O cilindro antigo foi retirado. Novo diâmetro configurado: **{st.session_state.diametro_cilindro:.2f} mm**"
    )
elif tonelagem_atual >= LIMITE_C:
    st.error(
        f"🚨 **CILINDRO PRONTO PARA TROCA!** Tonelagem atual: **{tonelagem_atual:,.0f} t**. "
        f"O operador deve realizar a troca no painel lateral e informar o novo diâmetro!"
    )
elif tonelagem_atual > LIMITE_B:
    st.warning("⚠️ **ATENÇÃO:** Cilindro em nível crítico de desgaste.")
elif tonelagem_atual > LIMITE_A:
    st.warning("⚠️ **ATENÇÃO:** Cilindro na faixa de alerta.")
else:
    st.success("✅ Cilindro operando dentro da faixa segura.")


# =========================
# INDICADORES PRINCIPAIS
# =========================
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Tonelagem Atual", f"{tonelagem_atual:,.0f} t")

with col2:
    st.metric("Diâmetro Atual", f"{st.session_state.diametro_cilindro:.1f} mm")

with col3:
    st.metric("Classificação ABC", f"{icone} {classe}")

with col4:
    st.metric("Situação", situacao)

with col5:
    st.metric("Estado", f"{icone_estado} {estado_atual}")


# =========================
# ESTADO DE OPERAÇÃO
# =========================
st.markdown("---")
st.subheader("⚙️ Estado de Operação")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if estado_atual == 1:
        st.success("🟢 ESTADO 1\n\nPRODUZINDO")
    else:
        st.info("Estado 1\n\nProduzindo")

with col2:
    if estado_atual == 2:
        st.warning("🟡 ESTADO 2\n\nSTAND-BY")
    else:
        st.info("Estado 2\n\nStand-by")

with col3:
    if estado_atual == 3:
        st.error("🔴 ESTADO 3\n\nFORA DO CENTRO")
    else:
        st.info("Estado 3\n\nFora do centro")

with col4:
    if estado_atual == 4:
        st.info("📦 ESTADO 4\n\nARMAZENAMENTO")
    else:
        st.info("Estado 4\n\nArmazenamento")


# =========================
# NÍVEL DE TONELAGEM
# =========================
st.markdown("---")
st.subheader("📊 Nível de Tonelagem")

porcentagem = min(tonelagem_atual / LIMITE_C, 1.0)
st.progress(porcentagem)

st.write(f"**{tonelagem_atual:,.0f} t** de **{LIMITE_C:,.0f} t**")


# =========================
# GRÁFICO
# =========================
st.markdown("---")
st.subheader("📈 Evolução da Tonelagem")

fig = criar_grafico(df)
st.plotly_chart(fig, use_container_width=True)


# =========================
# HISTÓRICO
# =========================
st.markdown("---")
st.subheader("📋 Histórico de Operação")

df_exibicao = df.copy()
df_exibicao["Tonelagem"] = df_exibicao["Tonelagem"].apply(
    lambda x: f"{x:,.0f} t"
)

df_exibicao = df_exibicao[
    [
        "Data",
        "Hora",
        "Tonelagem",
        "Classe",
        "Situação",
        "Estado",
        "Estado Nome",
    ]
]

st.dataframe(df_exibicao, use_container_width=True, hide_index=True)


# =========================
# EXPORTAÇÃO
# =========================
st.markdown("---")
st.subheader("📥 Exportação")

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Baixar histórico em CSV",
    data=csv,
    file_name="historico_dashboard.csv",
    mime="text/csv",
)
