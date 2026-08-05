import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ------------------------------
# ARQUIVOS DE DADOS
# ------------------------------
ARQ_ALUNOS = "alunos.csv"
ARQ_MENSAL = "mensalidades.csv"

def inicializar_arquivos():
    if not os.path.exists(ARQ_ALUNOS):
        pd.DataFrame(columns=[
            "id_aluno", "nome", "responsavel", "data_matricula",
            "ano_letivo", "valor_mensal", "qtd_parcelas", "mes_inicial", "turno"
        ]).to_csv(ARQ_ALUNOS, index=False)
    if not os.path.exists(ARQ_MENSAL):
        pd.DataFrame(columns=[
            "id_mensalidade", "id_aluno", "mes_ano", "valor",
            "vencimento", "data_pagamento", "status"
        ]).to_csv(ARQ_MENSAL, index=False)

def gerar_id(tabela):
    df = pd.read_csv(tabela)
    return 1 if df.empty else int(df.iloc[:,0].max() + 1)

# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

def data_valida(data):
    try: datetime.strptime(data, "%d/%m/%Y"); return True
    except: return False

NOMES_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LISTA_MESES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

# ------------------------------
# INICIALIZAR
# ------------------------------
inicializar_arquivos()
st.set_page_config(page_title="Controle Mensalidades - Web", layout="wide")
st.title("📚 Controle de Mensalidades - Versão Web")

# ------------------------------
# MENU LATERAL
# ------------------------------
menu = st.sidebar.selectbox("Menu", ["Alunos", "Mensalidades", "Relatórios"])

# ------------------------------
# TELA DE ALUNOS
# ------------------------------
if menu == "Alunos":
    st.subheader("Cadastro de Alunos")
    df_alunos = pd.read_csv(ARQ_ALUNOS)

    with st.form("form_aluno", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Completo")
        resp = col2.text_input("Responsável")
        col3, col4 = st.columns(2)
        dt_mat = col3.text_input("Data Matrícula", value=datetime.now().strftime("%d/%m/%Y"))
        ano = col4.number_input("Ano Letivo", value=datetime.now().year, min_value=2020)
        col5, col6, col7, col8 = st.columns(4)
        valor = col5.text_input("Valor Mensal R$", value="0,00")
        parcelas = col6.number_input("Nº Parcelas", value=12, min_value=1, max_value=24)
        mes_inic = col7.selectbox("Mês Inicial", NOMES_MESES, index=0)
        turno = col8.selectbox("Turno", ["Manhã", "Tarde", "Noite"])
        salvar = st.form_submit_button("💾 Salvar Aluno")

        if salvar:
            if not nome or not resp or not data_valida(dt_mat):
                st.error("Preencha todos os campos corretamente!")
            else:
                try:
                    valor_float = float(valor.replace(',', '.'))
                    mi_num = NOMES_MESES.index(mes_inic) + 1
                    novo_id = gerar_id(ARQ_ALUNOS)
                    novo_aluno = pd.DataFrame([{
                        "id_aluno": novo_id, "nome": nome, "responsavel": resp,
                        "data_matricula": dt_mat, "ano_letivo": int(ano),
                        "valor_mensal": valor_float, "qtd_parcelas": int(parcelas),
                        "mes_inicial": mi_num, "turno": turno
                    }])
                    df_alunos = pd.concat([df_alunos, novo_aluno], ignore_index=True)
                    df_alunos.to_csv(ARQ_ALUNOS, index=False)

                    # GERAR PARCELAS
                    df_mensal = pd.read_csv(ARQ_MENSAL)
                    base = mi_num - 1
                    for i in range(int(parcelas)):
                        m = (base + i) % 12
                        ma = f"{LISTA_MESES[m]}/{ano}"
                        ve = f"10/{LISTA_MESES[m]}/{ano}"
                        nova_parc = pd.DataFrame([{
                            "id_mensalidade": gerar_id(ARQ_MENSAL),
                            "id_aluno": novo_id, "mes_ano": ma, "valor": valor_float,
                            "vencimento": ve, "data_pagamento": None, "status": "A Receber"
                        }])
                        df_mensal = pd.concat([df_mensal, nova_parc], ignore_index=True)
                    df_mensal.to_csv(ARQ_MENSAL, index=False)

                    st.success("Aluno cadastrado! Vencimentos gerados para o dia 10 de cada mês.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.divider()
    st.subheader("Alunos Cadastrados")
    if not df_alunos.empty:
        for _, a in df_alunos.iterrows():
            with st.expander(f"{a['nome']} | {a['responsavel']}"):
                st.write(f"📅 Matrícula: {a['data_matricula']} | Ano: {a['ano_letivo']}")
                st.write(f"💰 Valor: {formatar_valor(a['valor_mensal'])} | Parcelas: {a['qtd_parcelas']}")
                st.write(f"📆 Início: {NOMES_MESES[int(a['mes_inicial'])-1]} | Turno: {a['turno']}")
                
                # CONFIRMAÇÃO EXCLUSÃO
                if f"conf_excl_{a['id_aluno']}" not in st.session_state:
                    st.session_state[f"conf_excl_{a['id_aluno']}"] = False
                
                if not st.session_state[f"conf_excl_{a['id_aluno']}"]:
                    if st.button(f"🗑️ Excluir {a['nome']}", key=f"btn_excl_{a['id_aluno']}"):
                        st.session_state[f"conf_excl_{a['id_aluno']}"] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Tem certeza que quer excluir este aluno e todas as suas mensalidades?")
                    col_nao, col_sim = st.columns(2)
                    if col_nao.button("❌ Não", key=f"nao_excl_{a['id_aluno']}"):
                        st.session_state[f"conf_excl_{a['id_aluno']}"] = False
                        st.rerun()
                    if col_sim.button("✅ Sim, excluir", key=f"sim_excl_{a['id_aluno']}"):
                        df_alunos = df_alunos[df_alunos["id_aluno"] != a["id_aluno"]]
                        df_mensal = pd.read_csv(ARQ_MENSAL)
                        df_mensal = df_mensal[df_mensal["id_aluno"] != a["id_aluno"]]
                        df_alunos.to_csv(ARQ_ALUNOS, index=False)
                        df_mensal.to_csv(ARQ_MENSAL, index=False)
                        st.success("Aluno e mensalidades excluídos!")
                        st.session_state[f"conf_excl_{a['id_aluno']}"] = False
                        st.rerun()
    else:
        st.info("Nenhum aluno cadastrado ainda.")

# ------------------------------
# TELA DE MENSALIDADES (SEM BOTÃO DAR BAIXA - SÓ EDITAR)
# ------------------------------
elif menu == "Mensalidades":
    st.subheader("Controle de Mensalidades")
    df_alunos = pd.read_csv(ARQ_ALUNOS)
    df_mensal = pd.read_csv(ARQ_MENSAL)
    if df_alunos.empty:
        st.warning("Cadastre um aluno primeiro!")
    else:
        id_escolhido = st.selectbox("Selecione o Aluno", df_alunos["nome"], index=0)
        id_aluno = df_alunos[df_alunos["nome"] == id_escolhido]["id_aluno"].values[0]
        mensais = df_mensal[df_mensal["id_aluno"] == id_aluno].sort_values("mes_ano")
        hoje = datetime.now().strftime("%d/%m/%Y")

        st.divider()
        for _, m in mensais.iterrows():
            status_exib = "Atrasada" if m["status"] == "A Receber" and data_valida(str(m["vencimento"])) and datetime.strptime(str(m["vencimento"]),"%d/%m/%Y") < datetime.strptime(hoje,"%d/%m/%Y") else m["status"]
            cor = "🔴" if status_exib == "Atrasada" else ("🟢" if status_exib == "Quitada" else "🟡")
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.write(f"**{m['mes_ano']}**")
                col2.write(formatar_valor(m["valor"]))
                col3.write(f"Venc: {m['vencimento']}")
                col4.write(f"{cor} {status_exib}")
                # ✅ SÓ FICA O BOTÃO EDITAR
                if col5.button(f"Editar", key=f"editar_{m['id_mensalidade']}_{m['mes_ano']}"):
                    st.session_state["editando"] = m
                if "editando" in st.session_state and st.session_state["editando"]["id_mensalidade"] == m["id_mensalidade"]:
                    with st.form(f"form_mensal_{m['id_mensalidade']}_{m['mes_ano']}", clear_on_submit=True):
                        novo_valor = st.text_input("Valor R$", value=str(m["valor"]).replace('.',','))
                        novo_venc = st.text_input("Vencimento", value=m["vencimento"])
                        novo_status = st.selectbox("Status", ["A Receber", "Quitada"], index=0 if m["status"]=="A Receber" else 1)
                        dt_pg = st.text_input("Data Pagamento", value=m["data_pagamento"] if m["status"]=="Quitada" else "")
                        if st.form_submit_button("Salvar Alteração"):
                            if not data_valida(novo_venc):
                                st.error("Data inválida! Use dd/mm/aaaa")
                            else:
                                df_mensal.loc[df_mensal["id_mensalidade"] == m["id_mensalidade"], ["valor", "vencimento", "status", "data_pagamento"]] = [
                                    float(novo_valor.replace(',','.')), novo_venc, novo_status, dt_pg if novo_status=="Quitada" else None
                                ]
                                df_mensal.to_csv(ARQ_MENSAL, index=False)
                                st.success("Atualizado com sucesso!")
                                del st.session_state["editando"]
                                st.rerun()

# ------------------------------
# RELATÓRIOS COM IMPRESSÃO
# ------------------------------
elif menu == "Relatórios":
    st.subheader("Relatórios")
    tipo = st.radio("Escolha", ["Todos", "A Receber", "Atrasadas", "Quitadas", "Por Período"], horizontal=True)
    df_alunos = pd.read_csv(ARQ_ALUNOS)
    df_mensal = pd.read_csv(ARQ_MENSAL)
    hoje = datetime.now().strftime("%d/%m/%Y")
    dados = None
    titulo_rel = ""

    if tipo == "Por Período":
        st.subheader("Filtrar por Período de Vencimento")
        col_d1, col_d2 = st.columns(2)
        dt_inicio = col_d1.text_input("Data Início (dd/mm/aaaa)", value="01/01/2026")
        dt_fim = col_d2.text_input("Data Fim (dd/mm/aaaa)", value=hoje)
        titulo_rel = f"Relatório de {dt_inicio} até {dt_fim}"
        if data_valida(dt_inicio) and data_valida(dt_fim):
            dados = df_mensal.merge(df_alunos, on="id_aluno", how="left")
            dados = dados[(dados["vencimento"] >= dt_inicio) & (dados["vencimento"] <= dt_fim)]
    elif tipo == "Todos":
        titulo_rel = "Relatório Geral de Mensalidades"
        dados = df_mensal.merge(df_alunos, on="id_aluno", how="left")
    elif tipo == "A Receber":
        titulo_rel = "Relatório - A Receber"
        dados = df_mensal.merge(df_alunos, on="id_aluno", how="left")
        dados = dados[(dados["status"] == "A Receber") & (dados["vencimento"] >= hoje)]
    elif tipo == "Atrasadas":
        titulo_rel = "Relatório - Atrasadas"
        dados = df_mensal.merge(df_alunos, on="id_aluno", how="left")
        dados = dados[(dados["status"] == "A Receber") & (dados["vencimento"] < hoje)]
    else:
        titulo_rel = "Relatório - Quitadas"
        dados = df_mensal.merge(df_alunos, on="id_aluno", how="left")
        dados = dados[dados["status"] == "Quitada"]

    if dados is not None and not dados.empty:
        exibe = dados[["nome", "mes_ano", "valor", "vencimento", "status"]].copy()
        exibe["valor"] = exibe["valor"].apply(formatar_valor)
        total = dados["valor"].sum()
        st.subheader(titulo_rel)
        st.dataframe(exibe, use_container_width=True)
        st.subheader(f"Total: {formatar_valor(total)}")

        st.divider()
        st.info("🖨️ Aperte Ctrl+P ou o ícone de impressora do navegador")
        if st.button("🖨️ Visualizar para Imprimir"):
            st.markdown(f"<h2 style='text-align:center;'>{titulo_rel}</h2><p style='text-align:center;'>Emitido em: {hoje}</p><hr>", unsafe_allow_html=True)
            st.table(exibe)
            st.markdown(f"<div style='text-align:right; font-weight:bold; font-size:18px;'>Total Geral: {formatar_valor(total)}</div>", unsafe_allow_html=True)
            st.success("✅ Agora imprima ou salve em PDF!")
    elif tipo != "Por Período" or (tipo == "Por Período" and data_valida(dt_inicio) and data_valida(dt_fim)):
        st.info("Sem registros para esse filtro.")