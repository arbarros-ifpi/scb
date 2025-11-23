import streamlit as st

# ========== CLASSES ==========
class Pessoa:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo  # "Física" ou "Jurídica"

class Conta:
    def __init__(self, numero, titular, saldo=0.0):
        self.numero = numero
        self.titular = titular
        self.saldo = saldo

    def depositar(self, valor):
        self.saldo += valor

    def sacar(self, valor):
        if valor <= self.saldo:
            self.saldo -= valor
            return True
        return False

    def transferir(self, destino, valor):
        if self.sacar(valor):
            destino.depositar(valor)
            return True
        return False

class ContaCorrente(Conta):
    def __init__(self, numero, titular, saldo=0.0):
        super().__init__(numero, titular, saldo - 50)

class ContaPoupanca(Conta):
    def render_juros(self):
        self.saldo *= 1.01

class ContaEspecial(Conta):
    def __init__(self, numero, titular, saldo=0.0, limite=500.0):
        super().__init__(numero, titular, saldo)
        self.limite = limite

    def sacar(self, valor):
        if valor <= self.saldo + self.limite:
            self.saldo -= valor
            return True
        return False


# ========== DADOS EM SESSÃO ==========
if "pessoas" not in st.session_state:
    st.session_state["pessoas"] = []

if "contas" not in st.session_state:
    st.session_state["contas"] = []


# ========== INTERFACE ==========
st.title("🏦 Sistema de Controle Bancário")

menu = st.sidebar.selectbox(
    "Menu",
    ["Cadastrar Pessoa", "Cadastrar Conta", "Operações", "Listar Contas"]
)

# ----- CADASTRAR PESSOA -----
if menu == "Cadastrar Pessoa":
    st.header("Cadastro de Pessoa")
    nome = st.text_input("Nome completo")
    tipo = st.radio("Tipo de pessoa", ["Física", "Jurídica"])

    if st.button("Cadastrar Pessoa"):
        if nome.strip() == "":
            st.warning("Informe o nome!")
        else:
            nova_pessoa = Pessoa(nome, tipo)
            st.session_state["pessoas"].append(nova_pessoa)
            st.success(f"{tipo} '{nome}' cadastrada com sucesso!")

# ----- CADASTRAR CONTA -----
elif menu == "Cadastrar Conta":
    st.header("Cadastro de Conta")

    if not st.session_state["pessoas"]:
        st.warning("⚠️ Nenhuma pessoa cadastrada ainda.")
    else:
        nomes_pessoas = [p.nome for p in st.session_state["pessoas"]]
        titular = st.selectbox("Titular", nomes_pessoas)
        tipo_conta = st.radio("Tipo de conta", ["Corrente", "Poupança", "Especial"])
        numero = len(st.session_state["contas"]) + 1

        if st.button("Criar Conta"):
            if tipo_conta == "Corrente":
                conta = ContaCorrente(numero, titular)
            elif tipo_conta == "Poupança":
                conta = ContaPoupanca(numero, titular)
            else:
                conta = ContaEspecial(numero, titular)
            st.session_state["contas"].append(conta)
            st.success(f"Conta {tipo_conta} criada com sucesso para {titular} (nº {numero})")

# ----- OPERAÇÕES -----
elif menu == "Operações":
    st.header("Operações Bancárias")

    if not st.session_state["contas"]:
        st.warning("⚠️ Nenhuma conta cadastrada ainda.")
    else:
        contas = st.session_state["contas"]
        conta_str = st.selectbox(
            "Selecione a conta",
            [f"{c.numero} - {c.titular}" for c in contas]
        )
        conta = next(c for c in contas if f"{c.numero} - {c.titular}" == conta_str)

        operacao = st.radio("Operação", ["Depósito", "Saque", "Transferência", "Render Juros"])
        valor = st.number_input("Valor (R$)", min_value=0.0, step=10.0)

        if operacao == "Depósito" and st.button("Executar Operação"):
            conta.depositar(valor)
            st.success(f"Depósito de R$ {valor:.2f} realizado.")

        elif operacao == "Saque" and st.button("Executar Operação"):
            if conta.sacar(valor):
                st.success(f"Saque de R$ {valor:.2f} realizado.")
            else:
                st.error("Saldo insuficiente.")

        elif operacao == "Transferência":
            destino_str = st.selectbox(
                "Conta de destino",
                [f"{c.numero} - {c.titular}" for c in contas if c != conta]
            )
            destino = next(c for c in contas if f"{c.numero} - {c.titular}" == destino_str)
            if st.button("Executar Transferência"):
                if conta.transferir(destino, valor):
                    st.success(f"Transferência de R$ {valor:.2f} para {destino.titular}.")
                else:
                    st.error("Saldo insuficiente.")

        elif operacao == "Render Juros" and st.button("Executar Operação"):
            if isinstance(conta, ContaPoupanca):
                conta.render_juros()
                st.success("Juros de 1% aplicados com sucesso!")
            else:
                st.warning("Apenas contas poupança rendem juros.")

        st.info(f"💰 Saldo atual: R$ {conta.saldo:.2f}")

# ----- LISTAR CONTAS -----
elif menu == "Listar Contas":
    st.header("Contas Cadastradas")
    if not st.session_state["contas"]:
        st.warning("Nenhuma conta cadastrada.")
    else:
        for c in st.session_state["contas"]:
            st.write(f"**Conta {c.numero}** - {c.titular} ({c.__class__.__name__}) - Saldo: R$ {c.saldo:.2f}")
