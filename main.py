import streamlit as st
import pandas as pd
import datetime
from pathlib import Path

# Título principal do dashboard
st.title("FinDash - Dashboard de Controle Financeiro")

# Subtítulo para contextualizar o objetivo do dashboard
st.write("Bem-vindo, organize suas finanças de forma simples e visual.")

# Verifica se as chaves do session_state já existem, caso contrário, cria com valores iniciais
if "transacoes" not in st.session_state:
    st.session_state.transacoes = pd.DataFrame(columns=["tipo", "Categoria", "Valor", "Data"])

if "config" not in st.session_state:
    st.session_state.config = {
        "tipos": ["Receita", "Despesa"],  # Mantendo apenas Receita e Despesa como tipos
        "categorias": ["Alimentação", "Lazer", "Transporte"]  # Categorias fixas
    }

# Caminho do arquivo CSV onde as transações serão armazenadas
arquivo_csv = Path("transacoes.csv")

# Função para carregar transações de um CSV
def carregar_transacoes(arquivo_csv):
    if arquivo_csv.exists():
        return pd.read_csv(arquivo_csv)
    else:
        return pd.DataFrame(columns=["tipo", "Categoria", "Valor", "Data"])

# Função para adicionar transação
def adicionar_transacao(tipo, categoria, valor, data):
    if data > datetime.date.today():
        st.error("A data não pode ser futura.")
        return
    nova_transacao = pd.DataFrame({
        "tipo": [tipo],
        "Categoria": [categoria],
        "Valor": [valor],
        "Data": [data.strftime('%Y-%m-%d')]
    })
    st.session_state.transacoes = pd.concat([st.session_state.transacoes, nova_transacao], ignore_index=True)
    st.success(f"{tipo} de R$ {valor:.2f} adicionada na categoria '{categoria}' em {data}.")
    # Salva automaticamente após adicionar a transação
    st.session_state.transacoes.to_csv(arquivo_csv, index=False)

# Carrega as transações do CSV ao iniciar
if arquivo_csv.exists():
    st.session_state.transacoes = carregar_transacoes(arquivo_csv)

# Barra lateral de navegação
with st.sidebar:
    opcao = st.radio("Escolha uma opção", [
        "Exibir Transações",
        "Adicionar Transação",
        "Editar Dados",
        "Excluir Dados",
        "Salvar",
        "Exportar para CSV"
    ])

# Adicionar Transação
if opcao == "Adicionar Transação":
    with st.form("add_form"):
        tipo = st.selectbox("Tipo de Transação:", st.session_state.config["tipos"])
        if tipo == "Receita" or tipo == "Despesa":
            categoria = st.text_input("Categoria:", placeholder="Digite uma categoria personalizada")
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = st.date_input("Data da Transação", value=datetime.date.today())

        submit_button = st.form_submit_button("Adicionar Transação")

        if submit_button:
            if not categoria:
                st.error("Por favor, preencha a categoria.")
            else:
                adicionar_transacao(tipo, categoria, valor, data)

# Exibir Transações
if opcao == "Exibir Transações":
    if not st.session_state.transacoes.empty:
        st.write("### Filtrar por Mês, Ano e Tipo")
        ano_atual = datetime.date.today().year
        mes_atual = datetime.date.today().month
        ano = st.selectbox("Ano", range(2020, datetime.date.today().year + 1), index=ano_atual - 2020)
        mes = st.selectbox("Mês", range(1, 13), index=mes_atual - 1)
        tipo = st.selectbox("Tipo de Transação", ["Ambos", "Receita", "Despesa"], index=0)

        # Filtrando as transações pelo mês e ano selecionados
        transacoes_filtradas = st.session_state.transacoes[
            pd.to_datetime(st.session_state.transacoes["Data"]).dt.year == ano
        ]
        transacoes_filtradas = transacoes_filtradas[
            pd.to_datetime(transacoes_filtradas["Data"]).dt.month == mes
        ]

        if tipo != "Ambos":
            transacoes_filtradas = transacoes_filtradas[transacoes_filtradas["tipo"] == tipo]

        st.dataframe(transacoes_filtradas)

        # Calculando a soma das receitas, despesas e o saldo
        soma_receitas = transacoes_filtradas[transacoes_filtradas["tipo"] == "Receita"]["Valor"].sum()
        soma_despesas = transacoes_filtradas[transacoes_filtradas["tipo"] == "Despesa"]["Valor"].sum()
        saldo = soma_receitas - soma_despesas

        st.write(f"### Resumo do mês {mes}/{ano}")
        st.write(f"Soma das Receitas: R$ {soma_receitas:.2f}")
        st.write(f"Soma das Despesas: R$ {soma_despesas:.2f}")
        st.write(f"**Saldo: R$ {saldo:.2f}**")

        if saldo >= 0:
            st.success(f"O saldo está positivo! (+R$ {saldo:.2f})")
        else:
            st.error(f"O saldo está negativo! (-R$ {saldo:.2f})")
    else:
        st.info("Nenhuma transação registrada ainda.")

# Editar Dados
if opcao == "Editar Dados":
    if not st.session_state.transacoes.empty:
        transacao_id = st.selectbox("Escolha a transação para editar",
                                    [(f"{idx} - {row['Categoria']} - {row['tipo']}", idx)
                                     for idx, row in st.session_state.transacoes.iterrows()])
        transacao = st.session_state.transacoes.loc[transacao_id[1]]

        with st.form("edit_form"):
            tipo_edit = st.selectbox("Tipo de Transação:", st.session_state.config["tipos"],
                                     index=st.session_state.config["tipos"].index(transacao["tipo"]))
            categoria_edit = st.text_input("Categoria", value=transacao["Categoria"])
            valor_edit = st.number_input("Valor (R$)", min_value=0.0, step=0.01, value=transacao["Valor"])
            data_edit = st.date_input("Data da Transação", value=pd.to_datetime(transacao["Data"]).date())

            submit_edit_button = st.form_submit_button("Atualizar Transação")

            if submit_edit_button:
                st.session_state.transacoes.at[transacao_id[1], "tipo"] = tipo_edit
                st.session_state.transacoes.at[transacao_id[1], "Categoria"] = categoria_edit
                st.session_state.transacoes.at[transacao_id[1], "Valor"] = valor_edit
                st.session_state.transacoes.at[transacao_id[1], "Data"] = str(data_edit)

                st.success("Transação atualizada com sucesso.")
                # Salva automaticamente após editar a transação
                st.session_state.transacoes.to_csv(arquivo_csv, index=False)
    else:
        st.info("Nenhuma transação registrada para editar.")


# Excluir Dados
if opcao == "Excluir Dados":
    if not st.session_state.transacoes.empty:
        transacao_id_excluir = st.selectbox("Escolha a transação para excluir",
                                            [(f"{idx} - {row['Categoria']} - {row['tipo']}", idx)
                                             for idx, row in st.session_state.transacoes.iterrows()])
        transacao_excluir = st.session_state.transacoes.loc[transacao_id_excluir[1]]

        confirmacao_exclusao = st.checkbox(
            f"Tem certeza que deseja excluir a transação de R$ {transacao_excluir['Valor']}?")

        if confirmacao_exclusao:
            if st.button("Confirmar Exclusão"):
                st.session_state.transacoes = st.session_state.transacoes.drop(transacao_id_excluir[1]).reset_index(
                    drop=True)
                st.success("Transação excluída com sucesso.")
                # Salva automaticamente após excluir a transação
                st.session_state.transacoes.to_csv(arquivo_csv, index=False)
        else:
            st.info("Marque o checkbox para confirmar a exclusão da transação.")
    else:
        st.info("Nenhuma transação registrada para excluir.")

# Salvar
if opcao == "Salvar":
    st.session_state.transacoes.to_csv(arquivo_csv, index=False)
    st.success("Dados salvos com sucesso.")

# Exportar para CSV
if opcao == "Exportar para CSV":
    if not st.session_state.transacoes.empty:
        st.download_button(
            label="Baixar Dados em CSV",
            data=st.session_state.transacoes.to_csv(index=False),
            file_name="transacoes.csv",
            mime="text/csv"
        )
    else:
        st.info("Não há transações para exportar.")


















