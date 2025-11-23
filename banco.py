import streamlit as st
import json
import os

# =========================================
#  FUNÇÕES DE PERSISTÊNCIA EM ARQUIVOS
# =========================================

def garantir_pasta():
    if not os.path.exists("data"):
        os.makedirs("data")

def carregar_arquivo(nome):
    garantir_pasta()
    caminho = f"data/{nome}"
    if not os.path.exists(caminho):
        with open(caminho, "w") as f:
            json.dump([], f)
    with open(caminho, "r") as f:
        return json.load(f)

def salvar_arquivo(nome, dados):
    with open(f"data/{nome}", "w") as f:
        json.dump(dados, f, indent=4)

def salvar_dados():
    salvar_arquivo("pessoas.json", [vars(p) for p in st.session_state["pessoas"]])

    contas_json = []
    for c in st.session_state["contas"]:
        contas_json.append({
            "numero": c.numero,
            "titular": c.titular,
            "saldo": c.saldo,
            "tipo": c.__class__.__name__,
            "limite": getattr(c, "limite", None)
        })

    salvar_arquivo("contas.json", contas_json)

# =========================================
#  CLASSES
# =========================================

class Pessoa:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo

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


# =========================================
#  CARREGAMENTO INICIAL DOS DADOS
# =========================================

if "pessoas" not in st.session_state:
    pessoas_json = carregar_arquivo("pessoas.json")
    st.session_state["pessoas"] = [Pessoa(p["nome"], p["tipo"]) for p in pessoas_json]

if "contas" not in st.session_state:
    contas_json = carregar_arquivo("contas.json")
    lista = []
    for c in contas_json:
        tipo = c["tipo"]
        if tipo == "ContaCorrente":
            obj = ContaCorrente(c["numero"], c["titular"], c["saldo"])
        elif tipo == "ContaPoupanca":
            obj = ContaPoupanca(c["numero"], c["titular"], c["saldo"])
        elif tipo == "ContaEspecial":
            obj = ContaEspecial(c["numero"], c["titular"], c["saldo"], c["limite"])
        lista.append(obj)
    st.session_state["contas"] = lista


# =========================================
#  INTERFACE STREAMLIT
# =========================================

st.title("🏦 Sistema Bancário — Versão 0.2 (com JSON)")

menu = st.sidebar.selectbox(
    "Menu", ["Cadastrar Pessoa", "Cadastrar Conta", "Operações", "Listar Contas"]
)

# -------------------------
# CADASTRAR PESSOA
# -------------------------
if menu == "Cadastrar Pessoa":
    st.header("Cadastro de Pessoa")
    nome = st.text_input("Nome completo")
    tipo = st.radio("Tipo", ["Física", "Jurídica"])

    if st.button("Cadastrar"):
        nova = Pessoa(nome, tipo)
        st.session_state["pessoas"].append(nova)
        salvar_dados()
        st.success(f"{tipo} '{nome}' cadastrada com sucesso!")


# -------------------------
# CADASTRAR CONTA
# -------------------------
elif menu == "Cadastrar Conta":
    st.header("Cadastro de Conta")

    if not st.session_state["pessoas"]:
        st.warning("Nenhuma pessoa cadastrada.")
    else:
        nomes = [p.nome for p in st.session_state["pessoas"]]
        titular = st.selectbox("Titular", nomes)
        tipo = st.radio("Tipo da conta", ["Corrente", "Poupança", "Especial"])
        numero = len(st.session_state["contas"]) + 1

        if st.button("Criar conta"):
            if tipo == "Corrente":
                conta = ContaCorrente(numero, titular)
            elif tipo == "Poupança":
                conta = ContaPoupanca(numero, titular)
            else:
                conta = ContaEspecial(numero, titular)

            st.session_state["contas"].append(conta)
            salvar_dados()
            st.success(f"Conta {tipo} criada (nº {numero}).")


# -------------------------
# OPERAÇÕES
# -------------------------
elif menu == "Operações":
    st.header("Operações Bancárias")

    if not st.session_state["contas"]:
        st.warning("Nenhuma conta cadastrada.")
    else:
        contas = st.session_state["contas"]
        lista = [f"{c.numero} - {c.titular}" for c in contas]

        conta_str = st.selectbox("Conta", lista)
        conta = next(c for c in contas if f"{c.numero} - {c.titular}" == conta_str)

        oper = st.radio("Operação", ["Depósito", "Saque", "Transferência", "Render Juros"])
        valor = st.number_input("Valor", min_value=0.0)

        if oper == "Depósito" and st.button("Executar"):
            conta.depositar(valor)
            salvar_dados()
            st.success("Depósito realizado.")

        elif oper == "Saque" and st.button("Executar"):
            if conta.sacar(valor):
                salvar_dados()
                st.success("Saque realizado.")
            else:
                st.error("Saldo insuficiente.")

        elif oper == "Transferência":
            destinos = [x for x in lista if x != conta_str]
            dest_str = st.selectbox("Destino", destinos)
            destino = next(c for c in contas if f"{c.numero} - {c.titular}" == dest_str)
            if st.button("Executar Transferência"):
                if conta.transferir(destino, valor):
                    salvar_dados()
                    st.success("Transferência realizada.")
                else:
                    st.error("Erro: saldo insuficiente.")

        elif oper == "Render Juros" and st.button("Executar"):
            if isinstance(conta, ContaPoupanca):
                conta.render_juros()
                salvar_dados()
                st.success("Juros aplicados.")
            else:
                st.warning("Somente poupança rende juros.")

        st.info(f"Saldo atual: R$ {conta.saldo:.2f}")


# -------------------------
# LISTAR CONTAS
# -------------------------
elif menu == "Listar Contas":
    st.header("Contas Cadastradas")
    for c in st.session_state["contas"]:
        st.write(f"**Conta {c.numero}** - {c.titular} ({c.__class__.__name__}) — Saldo: R$ {c.saldo:.2f}")
