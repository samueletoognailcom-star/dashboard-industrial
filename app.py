import random
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Gestão de Desgaste e Manutenção - CLP & Encoder",
    page_icon="⚙️",
    layout="wide",
)

# =========================
# LIMITES E METAS (Imagem)
# =========================
META_MAXIMA = 120_000
LIMITE_SEGURO = 102_000
LIMITE_ATENCAO = 110_000
LIMITE_CRITICO = 115_000
GATILHO_MANUTENCAO = 119_000


# =========================
# CLASSIFICAÇÃO DE ALERTA
# =========================
def classificar_tonelagem(tonelagem):
    if tonelagem <= LIMITE_SEGURO:
        return "Seguro (Verde)", "Operação Normal", "🟢", "success"
    elif tonelagem <= LIMITE_ATENCAO:
        return "Atenção (Amarelo)", "Monitoramento", "🟡", "warning"
    elif tonelagem <= LIMITE_CRITICO:
        return "Crítico (Vermelho)", "Manutenção Imediata", "🔴", "error"
    else:
        return (
            "Gatilho de Intervenção",
            "Manutenção Requerida / Troca",
            "🚨",
            "error",
        )


# =========================
# INICIALIZAÇÃO DO ESTADO DOS 6 CILINDROS
# =========================
if "cilindros" not in st.session_state:
    st.session_state.cilindros = {
        "Cilindro 1": {
            "diametro": 500.0,
            "tonelagem": 103500,
            "localizacao": "Em Operação (Centro de Usinagem)",
            "estado": "PRODUZINDO",
        },
        "Cilindro 2": {
            "diametro": 495.0,
            "tonelagem": 45000,
            "localizacao": "Stand-by / Reserva",
            "estado": "STAND-BY",
        },
        "Cilindro 3": {
            "diametro": 488.0,
            "tonelagem": 118500,
            "localizacao": "Stand-by / Reserva",
            "estado": "STAND-BY",
        },
        "Cilindro 4": {
            "diametro": 510.0,
            "tonelagem": 0,
            "localizacao": "Armazenamento / Retificado",
            "estado": "ARMAZENADO",
        },
        "Cilindro 5": {
            "diametro": 505.0,
            "tonelagem": 12000,
            "localizacao": "Armazenamento / Retificado",
            "estado": "ARMAZENADO",
        },
        "Cilindro 6": {
            "diametro": 492.0,
            "tonelagem": 0,
            "localizacao": "Armazenamento / Retificado",
            "estado": "ARMAZENADO",
        },
    }

if "cilindro_ativo" not in st.session_state:
    st.session_state.cilindro_ativo = "Cilindro 1"

if "historico" not in st.session_state:
    agora = datetime.now()
    st.session_state.historico = pd.DataFrame(
        [
            {
                "DataHora": agora - timedelta(minutes=(10 - i) * 15),
                "Cilindro": "Cilindro 1",
                "Tonelagem": 95000 + (i * 850),
                "Diâmetro": 500.0,
                "Status": "Operação Normal",
            }
            for i in range(10)
        ]
    )

cilindros = st.session_state.cilindros
cilindro_nome = st.session_state.cilindro_ativo
cilindro_dados = cilindros[cilindro_nome]

# =========================
# PAINEL LATERAL (CONTROLE E SELEÇÃO)
# =========================
with st.sidebar:
    st.title("⚙️ CLP & Encoder Controls")
    st.markdown("---")

    st.subheader("🎯 Seleção do Cilindro em Uso")
    cilindro_selecionado = st.selectbox(
        "Selecione o Cilindro no Centro de Usinagem:",
        list(cilindros.keys()),
        index=list(cilindros.keys()).index(cilindro_nome),
    )

    if cilindro_selecionado != st.session_state.cilindro_ativo:
        # Atualiza a localização do antigo para stand-by e do novo para operação
        cilindros[st.session_state.cilindro_ativo][
            "localizacao"
        ] = "Stand-by / Reserva"
        cilindros[st.session_state.cilindro_ativo]["estado"] = "STAND-BY"

        st.session_state.cilindro_ativo = cilindro_selecionado
        cilindros[cilindro_selecionado][
            "localizacao"
        ] = "Em Operação (Centro de Usinagem)"
        cilindros[cilindro_selecionado]["estado"] = "PRODUZINDO"
        st.rerun()

    st.markdown("---")
    st.subheader("🔧 Reset e Novo Ciclo (Manutenção)")

    novo_diametro = st.number_input(
        "Novo Diâmetro do Cilindro (mm):",
        min_value=100.0,
        max_value=2000.0,
        value=float(cilindro_dados["diametro"]),
        step=0.5,
    )

    if st.button("🔄 RESETAR TONELAGEM / NOVO CICLO"):
        cilindros[cilindro_nome]["diametro"] = novo_diametro
        cilindros[cilindro_nome]["tonelagem"] = 0
        cilindros[cilindro_nome]["estado"] = "PRODUZINDO"

        agora = datetime.now()
        nova_linha = pd.DataFrame(
            [
                {
                    "DataHora": agora,
                    "Cilindro": cilindro_nome,
                    "Tonelagem": 0,
                    "Diâmetro": novo_diametro,
                    "Status": "Novo Ciclo / Reset",
                }
            ]
        )
        st.session_state.historico = pd.concat(
            [st.session_state.historico, nova_linha], ignore_index=True
        )

        st.success(
            f"Reset efetuado com sucesso para o {cilindro_nome}! Novo diâmetro: {novo_diametro} mm"
        )
        st.rerun()

    st.markdown("---")
    st.subheader("📡 Simulação de Leitura do Encoder")
    if st.button("➕ Simular +1.500 Toneladas"):
        cilindros[cilindro_nome]["tonelagem"] += random.randint(1000, 2000)

        nivel, status, icone, _ = classificar_tonelagem(
            cilindros[cilindro_nome]["tonelagem"]
        )

        agora = datetime.now()
        nova_linha = pd.DataFrame(
            [
                {
                    "DataHora": agora,
                    "Cilindro": cilindro_nome,
                    "Tonelagem": cilindros[cilindro_nome]["tonelagem"],
                    "Diâmetro": cilindros[cilindro_nome]["diametro"],
                    "Status": status,
                }
            ]
        )
        st.session_state.historico = pd.concat(
            [st.session_state.historico, nova_linha], ignore_index=True
        )

        st.rerun()


# =========================
# CABEÇALHO DO DASHBOARD
# =========================
st.title("🏭 Monitoramento Industrial: CLP & Encoder")
st.subheader("Gestão de Desgaste e Manutenção")
st.caption(
    f"Cilindro Ativo: **{cilindro_nome}** | Diâmetro: **{cilindro_dados['diametro']} mm** | Localização: **{cilindro_dados['localizacao']}**"
)

st.markdown("---")


# =========================
# ALERTAS DE TONELAGEM (LAYOUT DA IMAGEM)
# =========================
tonelagem_atual = cilindro_dados["tonelagem"]
nivel, status, icone, cor_caixa = classificar_tonelagem(tonelagem_atual)

st.markdown("### 📊 Alertas de Tonelagem (Meta 120k)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🟢 Seguro (Verde)", "≤ 102.000 t", "Operação Normal")
with col2:
    st.metric("🟡 Atenção (Amarelo)", "110.000 t", "Monitoramento")
with col3:
    st.metric("🔴 Crítico (Vermelho)", "115.000 t", "Manutenção Imediata")
with col4:
    st.metric("🚨 Gatilho Intervenção", "119.000 t", "Parada/Troca")

# Barra de Progresso Personalizada com Nível da Imagem
porcentagem_barra = min(tonelagem_atual / META_MAXIMA, 1.0)
st.progress(porcentagem_barra)

st.write(
    f"**Tonelagem Acumulada Atual ({cilindro_nome}):** `{tonelagem_atual:,.0f} t` / `{META_MAXIMA:,.0f} t`"
)

if tonelagem_atual >= GATILHO_MANUTENCAO:
    st.error(
        f"🚨 **GATILHO DE INTERVENÇÃO ATINGIDO ({tonelagem_atual:,.0f} t)!**\n\n"
        f"O CLP sinalizou intervenção. O status mudou para **Manutenção Requerida**. "
        f"O mecânico/operador deve inserir o novo diâmetro no painel lateral e efetuar o reset."
    )
elif tonelagem_atual >= LIMITE_CRITICO:
    st.error(
        f"🔴 **STATUS CRÍTICO:** {tonelagem_atual:,.0f} t acumuladas. Manutenção imediata recomendada!"
    )
elif tonelagem_atual >= LIMITE_ATENCAO:
    st.warning(
        f"🟡 **STATUS ATENÇÃO:** {tonelagem_atual:,.0f} t acumuladas. Mantenha o monitoramento constante."
    )
else:
    st.success(
        f"🟢 **STATUS SEGURO:** {tonelagem_atual:,.0f} t acumuladas. Operação Normal."
    )


# =========================
# VISUALIZAÇÃO DOS 6 CILINDROS E SUAS LOCALIZAÇÕES
# =========================
st.markdown("---")
st.markdown("### 🏬 Status e Localização dos 6 Cilindros")

cols = st.columns(6)

for index, (nome_c, dados_c) in enumerate(cilindros.items()):
    with cols[index]:
        st.markdown(f"**{nome_c}**")
        st.caption(f"📏 {dados_c['diametro']} mm")
        st.write(f"**{dados_c['tonelagem']:,.0f} t**")

        # Badge de Estado / Localização
        if dados_c["estado"] == "PRODUZINDO":
            st.success("🟢 Em Operação")
        elif dados_c["estado"] == "STAND-BY":
            st.warning("🟡 Stand-by")
        else:
            st.info("📦 Armazenado")


# =========================
# GRÁFICO E DADOS HISTÓRICOS
# =========================
st.markdown("---")
st.markdown("### 📈 Evolução do Desgaste (Tonelagem Acumulada)")

df_hist = st.session_state.historico
df_cilindro_ativo = df_hist[df_hist["Cilindro"] == cilindro_nome]

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=df_cilindro_ativo["DataHora"],
        y=df_cilindro_ativo["Tonelagem"],
        mode="lines+markers",
        name="Tonelagem Acumulada",
        line=dict(color="#1f77b4", width=3),
    )
)

fig.add_hline(
    y=LIMITE_SEGURO,
    line_dash="dash",
    line_color="green",
    annotation_text="102k t (Seguro)",
)
fig.add_hline(
    y=LIMITE_ATENCAO,
    line_dash="dash",
    line_color="orange",
    annotation_text="110k t (Atenção)",
)
fig.add_hline(
    y=LIMITE_CRITICO,
    line_dash="dash",
    line_color="red",
    annotation_text="115k t (Crítico)",
)
fig.add_hline(
    y=GATILHO_MANUTENCAO,
    line_dash="solid",
    line_color="darkred",
    annotation_text="119k t (Gatilho Intervenção)",
)

fig.update_layout(
    title=f"Histórico de Desgaste do {cilindro_nome}",
    xaxis_title="Data / Horário",
    yaxis_title="Tonelagem (t)",
    height=400,
)

st.plotly_chart(fig, use_container_width=True)


# =========================
# TABELA DE REFERÊNCIA DE NÍVEIS
# =========================
st.markdown("---")
st.markdown("### 📋 Tabela de Controle de Alertas")

tabela_referencia = pd.DataFrame(
    [
        {
            "Nível de Alerta": "Seguro (Verde)",
            "Tonelagem Acumulada": "Até 102.000 t",
            "Status no Sistema": "Operação Normal",
        },
        {
            "Nível de Alerta": "Atenção (Amarelo)",
            "Tonelagem Acumulada": "110.000 t",
            "Status no Sistema": "Monitoramento",
        },
        {
            "Nível de Alerta": "Crítico (Vermelho)",
            "Tonelagem Acumulada": "115.000 t",
            "Status no Sistema": "Manutenção Imediata",
        },
        {
            "Nível de Alerta": "Gatilho de Intervenção",
            "Tonelagem Acumulada": "119.000 t",
            "Status no Sistema": "Manutenção Requerida / Parada",
        },
    ]
)

st.table(tabela_referencia)
