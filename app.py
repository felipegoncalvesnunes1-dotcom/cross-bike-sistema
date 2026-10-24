import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st

# ---------------- CONFIGURAÇÃO ----------------
st.set_page_config(
    page_title="Cross Bike - Sistema",
    page_icon="🚲",
    layout="wide",
)

PASTA_DADOS = Path("dados_cross_bike")
PASTA_DADOS.mkdir(exist_ok=True)
ARQUIVO_PRODUTOS = PASTA_DADOS / "produtos.json"
ARQUIVO_PONTO = PASTA_DADOS / "historico_ponto.json"


def carregar_json(caminho, padrao):
    """Carrega dados locais; se o arquivo não existir, usa o padrão informado."""
    try:
        if caminho.exists():
            with caminho.open("r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        st.warning(f"Não foi possível ler {caminho.name}. Os dados padrão serão usados.")
    return padrao


def salvar_json(caminho, dados):
    """Salva dados localmente em JSON."""
    try:
        with caminho.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    except OSError as erro:
        st.error(f"Não foi possível salvar os dados: {erro}")


PRODUTOS_INICIAIS = [
    {"Nome": "Pneu Mountain Bike 29", "Preço": 189.90},
    {"Nome": "Corrente Indexada 11v", "Preço": 149.00},
    {"Nome": "Pastilha de Freio", "Preço": 45.00},
]

if "produtos_cross" not in st.session_state:
    st.session_state.produtos_cross = carregar_json(ARQUIVO_PRODUTOS, PRODUTOS_INICIAIS)

if "historico_ponto" not in st.session_state:
    st.session_state.historico_ponto = carregar_json(ARQUIVO_PONTO, [])

if "itens_orcamento" not in st.session_state:
    st.session_state.itens_orcamento = []

# ---------------- VISUAL ----------------
st.markdown(
    """
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #FF6B00 !important; }
    .stButton > button {
        background-color: #FF6B00;
        color: white;
        border: 0;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #e65f00;
        color: white;
        border: 1px solid #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🚲 Cross Bike — Painel Oficial")
st.caption("Catálogo de peças • Orçamentos • Registro de ponto")

aba1, aba2, aba3 = st.tabs(
    ["📦 1. Cadastrar Peças", "📄 2. Criar Orçamento", "🕒 3. Bater Ponto & Histórico"]
)

# ---------------- ABA 1: CATÁLOGO ----------------
with aba1:
    st.header("Cadastrar novas peças")

    with st.form("form_nova_peca", clear_on_submit=True):
        col_nome, col_preco = st.columns(2)
        with col_nome:
            nome_nova_peca = st.text_input("Nome da peça", placeholder="Ex.: Pneu Aro 29")
        with col_preco:
            preco_nova_peca = st.number_input(
                "Preço (R$)", min_value=0.0, value=0.0, step=1.0, format="%.2f"
            )
        salvar_peca = st.form_submit_button("Salvar peça no catálogo")

    if salvar_peca:
        nome = nome_nova_peca.strip()
        if not nome:
            st.warning("Digite o nome da peça.")
        elif preco_nova_peca <= 0:
            st.warning("Informe um preço maior que zero.")
        else:
            st.session_state.produtos_cross.append(
                {"Nome": nome, "Preço": round(float(preco_nova_peca), 2)}
            )
            salvar_json(ARQUIVO_PRODUTOS, st.session_state.produtos_cross)
            st.success(f"Peça '{nome}' cadastrada por R$ {preco_nova_peca:.2f}.")

    st.divider()
    st.subheader("Peças cadastradas")

    if st.session_state.produtos_cross:
        for indice, produto in enumerate(st.session_state.produtos_cross):
            col_produto, col_excluir = st.columns([5, 1])
            col_produto.write(f"**{produto['Nome']}** — R$ {float(produto['Preço']):.2f}")
            if col_excluir.button("Excluir", key=f"excluir_produto_{indice}"):
                st.session_state.produtos_cross.pop(indice)
                salvar_json(ARQUIVO_PRODUTOS, st.session_state.produtos_cross)
                st.rerun()
    else:
        st.info("O catálogo ainda está vazio.")

# ---------------- ABA 2: ORÇAMENTO ----------------
with aba2:
    st.header("Gerador de orçamento")
    cliente = st.text_input("Nome do cliente", value="Cliente Cross Bike", key="nome_cliente")
    st.divider()
    st.subheader("🔍 Buscar e selecionar peças")

    pesquisa = st.text_input("Pesquisar peça", placeholder="Digite parte do nome ou deixe em branco")
    produtos_filtrados = [
        p for p in st.session_state.produtos_cross
        if pesquisa.strip().casefold() in p["Nome"].casefold()
    ]

    if produtos_filtrados:
        opcoes = [
            f"{p['Nome']} — R$ {float(p['Preço']):.2f}"
            for p in produtos_filtrados
        ]
        selecao = st.selectbox("Produto", opcoes)
        produto = produtos_filtrados[opcoes.index(selecao)]
        quantidade = st.number_input(
            "Quantidade", min_value=1, value=1, step=1, key="quantidade_orcamento"
        )

        col_adicionar, col_limpar = st.columns(2)
        with col_adicionar:
            if st.button("➕ Adicionar peça ao orçamento"):
                st.session_state.itens_orcamento.append({
                    "Quantidade": int(quantidade),
                    "Peça": produto["Nome"],
                    "Preço Unitário": float(produto["Preço"]),
                    "Total Item": round(float(produto["Preço"]) * int(quantidade), 2),
                })
                st.success("Peça adicionada ao orçamento.")
        with col_limpar:
            if st.button("🗑️ Limpar orçamento"):
                st.session_state.itens_orcamento = []
                st.rerun()
    else:
        st.info("Nenhuma peça encontrada. Cadastre uma peça na primeira aba.")

    if st.session_state.itens_orcamento:
        st.divider()
        st.subheader(f"Resumo do orçamento — {cliente.strip() or 'Cliente'}")

        total_geral = sum(item["Total Item"] for item in st.session_state.itens_orcamento)
        linhas = [
            f"Olá {cliente.strip() or 'Cliente'},",
            "Segue o orçamento solicitado na Cross Bike:",
            "",
        ]

        for item in st.session_state.itens_orcamento:
            st.write(
                f"✅ {item['Quantidade']}x {item['Peça']} — "
                f"R$ {item['Total Item']:.2f} "
                f"(R$ {item['Preço Unitário']:.2f} cada)"
            )
            linhas.append(
                f"• {item['Quantidade']}x {item['Peça']} — R$ {item['Total Item']:.2f}"
            )

        st.markdown(f"### 💰 Valor total: R$ {total_geral:.2f}")
        linhas.extend(["", f"Total geral: R$ {total_geral:.2f}", "", "Cross Bike"])
        st.text_area(
            "Texto para copiar e enviar ao cliente no WhatsApp",
            "\n".join(linhas),
            height=180,
        )
        st.caption("Selecione e copie o texto acima para enviar ao cliente.")

# ---------------- ABA 3: PONTO ----------------
with aba3:
    st.header("Ponto eletrônico da equipe")

    with st.form("form_ponto", clear_on_submit=True):
        funcionario = st.text_input("Nome do funcionário")
        acao = st.selectbox(
            "Ação do ponto",
            ["Entrada", "Saída para almoço", "Retorno do almoço", "Saída"],
        )
        registrar = st.form_submit_button("Confirmar registro de ponto")

    if registrar:
        nome_funcionario = funcionario.strip()
        if nome_funcionario:
            agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
            registro = {
                "Funcionário": nome_funcionario,
                "Ação": acao,
                "Data e hora": agora.strftime("%d/%m/%Y às %H:%M:%S"),
            }
            st.session_state.historico_ponto.append(registro)
            salvar_json(ARQUIVO_PONTO, st.session_state.historico_ponto)
            st.success(f"{acao} registrada para {nome_funcionario} às {registro['Data e hora']}.")
        else:
            st.error("Informe o nome do funcionário.")

    st.divider()
    st.subheader("📅 Histórico de pontos")

    if st.session_state.historico_ponto:
        st.dataframe(
            list(reversed(st.session_state.historico_ponto)),
            use_container_width=True,
            hide_index=True,
        )
        if st.button("Apagar todo o histórico de pontos"):
            st.session_state.historico_ponto = []
            salvar_json(ARQUIVO_PONTO, [])
            st.rerun()
    else:
        st.info("Nenhum ponto registrado ainda.")

st.caption("Os dados são salvos em arquivos locais na pasta dados_cross_bike.")
