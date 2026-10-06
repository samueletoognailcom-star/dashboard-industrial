import random
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# =========================
# CONFIGURAÇÃO E METAS
# =========================
st.set_page_config(
    page_title="CLP & Encoder - Monitoramento", page_icon="⚙️", layout="wide"
)

META_MAXIMA = 120_000
LIMITE_SEGURO = 102_000
LIMITE_ATENCAO = 110_000
LIMITE_CRITICO = 115_000
GATILHO_MANUTENCAO = 119_000


# =========================
# BANCO DE DADOS (SQLite)
# =========================
def conectar_bd():
    return sqlite3.connect("fabrica.db")


def inicializar_banco():
    with conectar_bd() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cilindros (
                nome TEXT PRIMARY KEY,
                diametro REAL,
                tonelagem REAL,
                estado TEXT
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT,
                cilindro TEXT,
                tonelagem REAL,
                diametro REAL,
                status TEXT
            )
        """
        )

        cursor.execute("SELECT COUNT(*) FROM cilindros")
        if cursor.fetchone()[0] == 0:
            cilindros_iniciais = [
                ("Cilindro 1", 500.0, 103500.0, "EM USO"),
                ("Cilindro 2", 495.0, 45000.0, "STAND-BY"),
                ("Cilindro 3", 488.0, 118500.0, "STAND-BY"),
                ("Cilindro 4", 510.0, 0.0, "ARMAZENADO"),
                ("Cilindro 5", 505.0, 12000.0, "ARMAZENADO"),
                ("Cilindro 6", 492.0, 0.0, "ARMAZENADO"),
            ]
            cursor.executemany(
                "INSERT INTO cilindros VALUES (?, ?, ?, ?)", cilindros_iniciais
            )


inicializar_banco()


def obter_cilindros():
    with conectar_bd() as conn:
        df = pd.read_sql_query("SELECT * FROM cilindros", conn)
    return df.set_index("nome").to_dict("index")


def atualizar_cilindro(nome, **kwargs):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        for campo, valor in kwargs.items():
            cursor.execute(
                f"UPDATE cilindros SET {campo} = ? WHERE nome = ?",
                (valor, nome),
            )


def salvar_historico(cilindro, tonelagem, diametro, status):
    with conectar_bd() as conn:
        cursor = conn.cursor()
        agora = datetime.now().strftime("%d/%m/%Y %H:%M")
        cursor.execute(
            """
            INSERT INTO historico (data_hora, cilindro, tonelagem, diametro, status)
            VALUES (?, ?, ?, ?, ?)
        """,
            (agora, cilindro, tonelagem, diametro, status),
        )


def obter_historico():
    with conectar_bd() as conn:
        return pd.read_sql_query(
            "SELECT data_hora as 'Data/Hora', cilindro as 'Cilindro', tonelagem as 'Tonelagem (t)', diametro as 'Diâmetro (mm)', status as 'Status' FROM historico ORDER BY id DESC",
            conn,
        )


def classificar(tonelagem):
    if tonelagem <= LIMITE_SEGURO:
        return "🟢 Seguro", "Operação Normal"
    elif tonelagem <= LIMITE_ATENCAO:
        return "🟡 Atenção", "Monitoramento"
    elif tonelagem <= LIMITE_CRITICO:
        return "🔴 Crítico", "Manutenção Imediata"
    else:
        return "🚨 Intervenção", "Manutenção Requerida"


# =========================
# CONTROLE LATERAL
# =========================
cilindros = obter_cilindros()

if "cilindro_ativo" not in st.session_state:
    st.session_state.cilindro_ativo = "Cilindro 1"

cilindro_nome = st.session_state.cilindro_ativo
cilindro_dados = cilindros[cilindro_nome]

with st.sidebar:
    st.title("⚙️ Painel CLP")

    # Seleção do cilindro
    novo_ativo = st.selectbox(
        "Cilindro em Uso:",
        list(cilindros.keys()),
        index=list(cilindros.keys()).index(cilindro_nome),
    )
    if novo_ativo != cilindro_nome:
        atualizar_cilindro(cilindro_nome, estado="STAND-BY")
        atualizar_cilindro(novo_ativo, estado="EM USO")
        st.session_state.cilindro_ativo = novo_ativo
        st.rerun()

    st.markdown("---")
    st.subheader("🔧 Manutenção / Reset")
    novo_diam = st.number_input(
        "Novo Diâmetro (mm):",
        value=float(cilindro_dados["diametro"]),
        step=0.5,
    )

    if st.button("🔄 Resetar Tonelagem"):
        atualizar_cilindro(
            cilindro_nome, diametro=novo_diam, tonelagem=0, estado="EM USO"
        )
        salvar_historico(cilindro_nome, 0, novo_diam, "Reset / Novo Ciclo")
        st.success("Ciclo resetado!")
        st.rerun()

    st.markdown("---")
    if st.button("➕ Simular Leitura (+1.500t)"):
        nova_ton = cilindro_dados["tonelagem"] + random.randint(1000, 2000)
        _, status = classificar(nova_ton)
        atualizar_cilindro(cilindro_nome, tonelagem=nova_ton)
        salvar_historico(
            cilindro_nome, nova_ton, cilindro_dados["diametro"], status
        )
        st.rerun()


# =========================
# PAINEL PRINCIPAL
# =========================
st.title("🏭 Monitoramento de Desgaste - CLP & Encoder")

# Status do Cilindro Ativo
tonelagem_atual = cilindro_dados["tonelagem"]
nivel, status = classificar(tonelagem_atual)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Cilindro em Uso", cilindro_nome)
col2.metric("Diâmetro Atual", f"{cilindro_dados['diametro']} mm")
col3.metric("Tonelagem Acumulada", f"{tonelagem_atual:,.0f} t")
col4.metric("Status no Sistema", f"{nivel} | {status}")

# Barra de Progresso
st.progress(min(tonelagem_atual / META_MAXIMA, 1.0))

# Alerta caso atinja o gatilho
if tonelagem_atual >= GATILHO_MANUTENCAO:
    st.error(
        f"🚨 **GATILHO DE INTERVENÇÃO ATINGIDO ({tonelagem_atual:,.0f} t)!** Realize a manutenção e o reset no painel lateral."
    )

st.markdown("---")

# Visualização Enxuta dos 6 Cilindros
st.subheader("📦 Visão Geral dos 6 Cilindros")
cols = st.columns(6)
for idx, (nome, dados) in enumerate(cilindros.items()):
    with cols[idx]:
        st.markdown(f"**{nome}**")
        st.caption(f"📏 {dados['diametro']} mm")
        st.write(f"**{dados['tonelagem']:,.0f} t**")
        if dados["estado"] == "EM USO":
            st.success("Em Uso")
        elif dados["estado"] == "STAND-BY":
            st.warning("Stand-by")
        else:
            st.info("Armazenado")

st.markdown("---")

# Gráfico de Linha Enxuto
st.subheader("📈 Histórico de Desgaste")
df_hist = obter_historico()
df_cil = df_hist[df_hist["Cilindro"] == cilindro_nome]

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df_cil["Data/Hora"],
        y=df_cil["Tonelagem (t)"],
        mode="lines+markers",
        name="Tonelagem",
    )
)
fig.add_hline(
    y=LIMITE_SEGURO, line_dash="dash", line_color="green", annotation_text="102k"
)
fig.add_hline(
    y=LIMITE_ATENCAO, line_dash="dash", line_color="orange", annotation_text="110k"
)
fig.add_hline(
    y=LIMITE_CRITICO, line_dash="dash", line_color="red", annotation_text="115k"
)
fig.add_hline(
    y=GATILHO_MANUTENCAO,
    line_dash="solid",
    line_color="darkred",
    annotation_text="119k",
)
fig.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
st.plotly_chart(fig, use_container_width=True)

# Tabela do Banco de Dados
with st.expander("📋 Ver Tabela do Banco de Dados"):
    st.dataframe(df_hist, use_container_width=True, hide_index=True)
