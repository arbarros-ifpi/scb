import streamlit as st

# -----------------------------
# DADOS EM MEMÓRIA
# -----------------------------
pessoas = []
contas = []
contador_contas = 1

# -----------------------------
# CLASSES
# -----------------------------
class Pessoa:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo  # "Física" ou "Jurídica"

class ContaBancaria:
    def __init__(self, numero, pessoa, tipo):
        self.numero = numero
        self.pessoa = pessoa
        self.tipo = tipo
        self.saldo = 0.0
        self.historico = []

        if self.tipo == "Conta Corrente":
            self.saldo -= 50
            self.historico.append("Tarifa de abertura: R$ 50,00")

    def depositar(self, valor):
        self.saldo += valor
        self.historico.append(f"Depósito: R$ {valor:.2f}")

    def sacar(self, valor):
        limite = 0
        if self.tipo == "Conta Especial":
            limite = 500

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
        if self.tipo == "Conta Poupança":
            juros = self.saldo * 0.01
            self.saldo += juros
            self.historico.append(f"Rendimento de 1%: R$ {juros:.2f}")

# -----------------------------
# INTERFACE STREAMLIT
# -----------------------------
st.title("Sistema Bancário – Com Extrato")

menu = st.sidebar.selectbox("Menu", ["Cadastrar Pessoa", "Cadastrar Conta", "Operações", "Extrato"])

# -----------------------------
# CADASTRAR PESSOA
# -----------------------------
if menu == "Cadastrar Pessoa":
    st.header("Cadastro de Pessoa")

    nome = st.text_input("Nome")
    tipo = st.selectbox("Tipo", ["Física", "Jurídica"])

    if st.button("Cadastrar Pessoa"):
        pessoas.append(Pessoa(nome, tipo))
        st.success("Pessoa cadastrada com sucesso!")

# -----------------------------
# CADASTRAR CONTA
# -----------------------------
elif menu == "Cadastrar Conta":
    st.header("Cadastro de Conta")

    if len(pessoas) == 0:
        st.warning("Nenhuma pessoa cadastrada!")
    else:
        pessoa_nomes = [p.nome for p in pessoas]
        pessoa_escolhida = st.selectbox("Selecione a pessoa", pessoa_nomes)
        tipo_conta = st.selectbox("Tipo de Conta", ["Conta Corrente", "Conta Poupança", "Conta Especial"])

        if st.button("Criar Conta"):
            global contador_contas
            pessoa = next(p for p in pessoas if p.nome == pessoa_escolhida)
            nova_conta = ContaBancaria(contador_contas, pessoa, tipo_conta)
            contas.append(nova_conta)
            contador_contas += 1
            st.success("Conta criada com sucesso!")

# -----------------------------
# OPERAÇÕES (Saque, Depósito, Transferência)
# -----------------------------
elif menu == "Operações":
    st.header("Operações Bancárias")

    if len(contas) == 0:
        st.warning("Nenhuma conta cadastrada!")
    else:
        lista_contas = [f"{c.numero} - {c.pessoa.nome}" for c in contas]
        escolha = st.selectbox("Selecione a conta", lista_contas)
        conta = contas[lista_contas.index(escolha)]

        st.write(f"Saldo atual: **R$ {conta.saldo:.2f}**")

        operacao = st.selectbox("Operação", ["Depósito", "Saque", "Transferência"])
        valor = st.number_input("Valor", min_value=0.0)

        if operacao == "Depósito":
            if st.button("Depositar"):
                conta.depositar(valor)
                st.success("Depósito realizado!")

        elif operacao == "Saque":
            if st.button("Sacar"):
                if conta.sacar(valor):
                    st.success("Saque realizado!")
                else:
                    st.error("Saldo insuficiente!")

        elif operacao == "Transferência":
            outras_contas = [c for c in contas if c != conta]
            contas_destino_nomes = [f"{c.numero} - {c.pessoa.nome}" for c in outras_contas]
            
            if len(outras_contas) == 0:
                st.warning("Nenhuma outra conta disponível para transferência!")
            else:
                destino_nome = st.selectbox("Conta destino", contas_destino_nomes)
                conta_destino = outras_contas[contas_destino_nomes.index(destino_nome)]

                if st.button("Transferir"):
                    if conta.transferir(conta_destino, valor):
                        st.success("Transferência realizada!")
                    else:
                        st.error("Saldo insuficiente!")

# -----------------------------
# EXTRATO
# -----------------------------
elif menu == "Extrato":
    st.header("Extrato da Conta")

    if len(contas) == 0:
        st.warning("Nenhuma conta cadastrada!")
    else:
        lista_contas = [f"{c.numero} - {c.pessoa.nome}" for c in contas]
        escolha = st.selectbox("Selecione a conta", lista_contas)
        conta = contas[lista_contas.index(escolha)]

        st.subheader("Extrato de Operações")
        for item in conta.historico:
            st.write("- " + item)

        st.subheader("Saldo Final")
        st.write(f"**R$ {conta.saldo:.2f}**")
