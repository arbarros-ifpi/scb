"""
App Streamlit: Sistema Bancário Integrado
- Persistência em JSON
- Extrato / Histórico
- Geração de PDF (ReportLab)
- Interface estilizada com imagem de cabeçalho (arquivo local provido)

Requisitos:
- streamlit
- reportlab

No terminal (env ativado):
pip install streamlit reportlab
streamlit run app_streamlit_banco_integrado.py
"""

import streamlit as st
import json
import os
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# -----------------------------
# CONFIG
# -----------------------------
DATA_DIR = "data"
PESSOAS_FILE = os.path.join(DATA_DIR, "pessoas.json")
CONTAS_FILE = os.path.join(DATA_DIR, "contas.json")
# caminho do arquivo enviado pelo usuário (usado como header).
HEADER_IMG = "/mnt/data/ffc622cb-89dd-4f43-87f6-d67339a7f787.png"

# -----------------------------
# UTILITÁRIOS DE ARQUIVO
# -----------------------------

def garantir_pasta():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def carregar_json(caminho):
    garantir_pasta()
    if not os.path.exists(caminho):
        with open(caminho, "w") as f:
            json.dump([], f)
    with open(caminho, "r") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    garantir_pasta()
    with open(caminho, "w") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# -----------------------------
# CLASSES
# -----------------------------
class Pessoa:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo

    def to_dict(self):
        return {"nome": self.nome, "tipo": self.tipo}

    @staticmethod
    def from_dict(d):
        return Pessoa(d["nome"], d["tipo"]) 


class Conta:
    def __init__(self, numero, titular_nome, tipo, saldo=0.0, historico=None, limite=None):
        self.numero = numero
        self.titular = titular_nome
        self.tipo = tipo
        self.saldo = float(saldo)
        self.historico = historico if historico is not None else []
        self.limite = limite

        # tarifa inicial para conta corrente (apenas se historico vazio)
        if self.tipo == "Corrente" and not any("Tarifa" in h for h in self.historico):
            self.saldo -= 50
            self.historico.insert(0, "Tarifa de abertura: R$ 50,00")

    def depositar(self, valor):
        self.saldo += valor
        self.historico.append(f"Depósito: R$ {valor:.2f}")

    def sacar(self, valor):
        limite = 0.0
        if self.tipo == "Especial":
            limite = float(self.limite or 500.0)

        if self.saldo + limite >= valor:
            self.saldo -= valor
            self.historico.append(f"Saque: R$ {valor:.2f}")
            return True
        return False

    def transferir(self, destino, valor):
        if self.sacar(valor):
            destino.depositar(valor)
            self.historico.append(f"Transferência enviada para conta {destino.numero}: R$ {valor:.2f}")
            destino.historico.append(f"Transferência recebida da conta {self.numero}: R$ {valor:.2f}")
            return True
        return False

    def render_juros(self):
        if self.tipo == "Poupanca":
            juros = self.saldo * 0.01
            self.saldo += juros
            self.historico.append(f"Rendimento de 1%: R$ {juros:.2f}")
            return juros
        return 0.0

    def to_dict(self):
        return {
            "numero": self.numero,
            "titular": self.titular,
            "tipo": self.tipo,
            "saldo": self.saldo,
            "historico": self.historico,
            "limite": self.limite,
        }

    @staticmethod
    def from_dict(d):
        return Conta(d["numero"], d["titular"], d["tipo"], saldo=d.get("saldo", 0.0), historico=d.get("historico", []), limite=d.get("limite"))

# -----------------------------
# PERSISTÊNCIA + SESSION STATE
# -----------------------------

if "pessoas" not in st.session_state:
    pessoas_json = carregar_json(PESSOAS_FILE)
    st.session_state.pessoas = [Pessoa.from_dict(p) for p in pessoas_json]

if "contas" not in st.session_state:
    contas_json = carregar_json(CONTAS_FILE)
    st.session_state.contas = [Conta.from_dict(c) for c in contas_json]


def salvar_tudo():
    salvar_json(PESSOAS_FILE, [p.to_dict() for p in st.session_state.pessoas])
    salvar_json(CONTAS_FILE, [c.to_dict() for c in st.session_state.contas])

# -----------------------------
# FUNÇÃO: GERAR PDF
# -----------------------------

def gerar_pdf_extrato(conta: Conta):
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, f"extrato_conta_{conta.numero}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    largura, altura = A4
    y = altura - 50

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Extrato da Conta {conta.numero}")
    y -= 30

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Cliente: {conta.titular}")
    y -= 20
    c.drawString(50, y, f"Tipo de conta: {conta.tipo}")
    y -= 20
    c.drawString(50, y, f"Saldo atual: R$ {conta.saldo:.2f}")
    y -= 30

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Histórico de Operações:")
    y -= 24

    c.setFont("Helvetica", 11)
    for item in conta.historico:
        if y < 60:
            c.showPage()
            y = altura - 50
            c.setFont("Helvetica", 11)
        c.drawString(50, y, f"- {item}")
        y -= 18

    c.save()
    return pdf_path

# -----------------------------
# UI Helpers (cards, styles)
# -----------------------------

def css():
    st.markdown(
        """
        <style>
        .card { background: #F8FFF8; padding: 14px; border-radius: 12px; border-left:6px solid #2E8B57; margin-bottom:12px }
        .small { font-size:0.9rem; color: #555555 }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card(title, subtitle="", icon="", color="#2E8B57"):
    st.markdown(f"""
    <div class='card'>
        <h3 style='margin:0'>{icon} {title}</h3>
        <div class='small'>{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# INÍCIO DO APP
# -----------------------------

st.set_page_config(page_title="Sistema Bancário", layout="wide")
css()

# Cabeçalho (usa o arquivo local enviado)
if os.path.exists(HEADER_IMG):
    st.image(HEADER_IMG, use_column_width=True)
else:
    st.markdown("<h1>Sistema Bancário</h1>", unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center; color:#2E8B57;'>Controle Bancário Educacional</h2>", unsafe_allow_html=True)
st.sidebar.markdown("""
<div style='text-align:center;'>
  <img src='https://img.icons8.com/ios-filled/100/2E8B57/bank.png' width='80'>
  <h3 style='color:#2E8B57;'>Menu</h3>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.selectbox("Menu", ["Dashboard", "Cadastrar Pessoa", "Cadastrar Conta", "Operações", "Extrato", "Configurações"])

# -----------------------------
# DASHBOARD
# -----------------------------
if menu == "Dashboard":
    st.header("Resumo")
    col1, col2, col3 = st.columns(3)
    with col1:
        card("Clientes cadastrados", str(len(st.session_state.pessoas)), icon="👥")
    with col2:
        card("Contas cadastradas", str(len(st.session_state.contas)), icon="🏦")
    with col3:
        total_dinheiro = sum(c.saldo for c in st.session_state.contas)
        card("Total em Saldos", f"R$ {total_dinheiro:.2f}", icon="💰")

# -----------------------------
# CADASTRAR PESSOA
# -----------------------------
elif menu == "Cadastrar Pessoa":
    st.header("Cadastro de Pessoa")
    col1, col2 = st.columns([3,1])
    with col1:
        nome = st.text_input("Nome completo")
        tipo = st.selectbox("Tipo", ["Física", "Jurídica"]) 
    with col2:
        if st.button("➕ Cadastrar Pessoa"):
            if not nome.strip():
                st.warning("Informe o nome!")
            else:
                st.session_state.pessoas.append(Pessoa(nome.strip(), tipo))
                salvar_tudo()
                st.success(f"Pessoa '{nome.strip()}' cadastrada.")

    if st.session_state.pessoas:
        st.markdown("### Pessoas cadastradas")
        for p in st.session_state.pessoas:
            st.write(f"- {p.nome} ({p.tipo})")

# -----------------------------
# CADASTRAR CONTA
# -----------------------------
elif menu == "Cadastrar Conta":
    st.header("Cadastro de Conta")
    if not st.session_state.pessoas:
        st.warning("Cadastre uma pessoa antes de criar contas.")
    else:
        nomes = [p.nome for p in st.session_state.pessoas]
        titular = st.selectbox("Titular", nomes)
        tipo_conta = st.selectbox("Tipo de conta", ["Corrente", "Poupanca", "Especial"])

        if st.button("➕ Criar Conta"):
            numero = 1 + (max([c.numero for c in st.session_state.contas]) if st.session_state.contas else 0)
            limite = 500.0 if tipo_conta == "Especial" else None
            conta = Conta(numero, titular, tipo_conta, saldo=0.0, historico=[], limite=limite)
            st.session_state.contas.append(conta)
            salvar_tudo()
            st.success(f"Conta {numero} ({tipo_conta}) criada para {titular}.")

# -----------------------------
# OPERAÇÕES
# -----------------------------
elif menu == "Operações":
    st.header("Operações")
    if not st.session_state.contas:
        st.warning("Cadastre pelo menos uma conta.")
    else:
        lista = [f"{c.numero} - {c.titular}" for c in st.session_state.contas]
        conta_sel = st.selectbox("Conta", lista)
        conta = next(c for c in st.session_state.contas if f"{c.numero} - {c.titular}" == conta_sel)

        st.metric("Saldo", f"R$ {conta.saldo:.2f}")
        col1, col2 = st.columns(2)
        with col1:
            oper = st.selectbox("Operação", ["Depósito", "Saque", "Transferência", "Render Juros"])
            valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        with col2:
            if oper == "Transferência":
                destinos = [x for x in lista if x != conta_sel]
                destino_sel = st.selectbox("Destino", destinos) if destinos else None

        if st.button("Executar"):
            if oper == "Depósito":
                conta.depositar(valor)
                salvar_tudo()
                st.success("Depósito realizado.")
            elif oper == "Saque":
                if conta.sacar(valor):
                    salvar_tudo()
                    st.success("Saque realizado.")
                else:
                    st.error("Saldo insuficiente.")
            elif oper == "Transferência":
                if not destinos:
                    st.warning("Sem contas de destino disponíveis.")
                else:
                    destino = next(c for c in st.session_state.contas if f"{c.numero} - {c.titular}" == destino_sel)
                    if conta.transferir(destino, valor):
                        salvar_tudo()
                        st.success("Transferência realizada.")
                    else:
                        st.error("Saldo insuficiente.")
            elif oper == "Render Juros":
                juros = conta.render_juros()
                if juros > 0:
                    salvar_tudo()
                    st.success(f"Juros aplicados: R$ {juros:.2f}")
                else:
                    st.warning("Apenas contas Poupanca rendem juros.")

# -----------------------------
# EXTRATO
# -----------------------------
elif menu == "Extrato":
    st.header("Extrato e PDF")
    if not st.session_state.contas:
        st.warning("Nenhuma conta cadastrada.")
    else:
        lista = [f"{c.numero} - {c.titular}" for c in st.session_state.contas]
        conta_sel = st.selectbox("Conta", lista)
        conta = next(c for c in st.session_state.contas if f"{c.numero} - {c.titular}" == conta_sel)

        st.subheader(f"Extrato da conta {conta.numero} - {conta.titular}")
        st.write(f"Tipo: **{conta.tipo}**")
        st.write(f"Saldo atual: **R$ {conta.saldo:.2f}**")

        st.markdown("---")
        st.subheader("Histórico")
        if conta.historico:
            for item in reversed(conta.historico):
                st.write(f"- {item}")
        else:
            st.write("Nenhuma operação registrada.")

        st.markdown("---")
        if st.button("Gerar PDF do Extrato"):
            pdf_path = gerar_pdf_extrato(conta)
            with open(pdf_path, "rb") as f:
                st.download_button("Baixar PDF", f, file_name=f"extrato_conta_{conta.numero}.pdf", mime="application/pdf")

# -----------------------------
# CONFIGURAÇÕES
# -----------------------------
elif menu == "Configurações":
    st.header("Configurações")
    st.markdown("- Dados são salvos em `data/pessoas.json` e `data/contas.json`.")
    st.markdown(f"- Imagem de cabeçalho usada: `{HEADER_IMG}`")
    if st.button("Exportar dados (JSON)"):
        salvar_tudo()
        with open(PESSOAS_FILE, "rb") as fp1, open(CONTAS_FILE, "rb") as fp2:
            st.download_button("Baixar pessoas.json", fp1, file_name="pessoas.json", mime="application/json")
            st.download_button("Baixar contas.json", fp2, file_name="contas.json", mime="application/json")

# -----------------------------
# RODAPÉ
# -----------------------------
st.markdown("<hr style='border:1px solid #E0E0E0;'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center; color:gray;'><small>Desenvolvido para fins educacionais • IFPI</small></div>", unsafe_allow_html=True)
