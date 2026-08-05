import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ------------------------------
# BANCO EXCLUSIVO DO STREAMLIT
# ------------------------------
ARQ_DB = 'controle_streamlit.db'

def conectar():
    return sqlite3.connect(ARQ_DB, timeout=5)

def criar_banco():
    conn = conectar()
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS alunos (
        id_aluno INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        responsavel TEXT NOT NULL,
        data_matricula TEXT NOT NULL,
        ano_letivo INTEGER NOT NULL,
        valor_mensal REAL NOT NULL,
        qtd_parcelas INTEGER NOT NULL,
        mes_inicial INTEGER NOT NULL,
        turno TEXT NOT NULL
    )''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS mensalidades (
        id_mensalidade INTEGER PRIMARY KEY AUTOINCREMENT,
        id_aluno INTEGER NOT NULL,
        mes_ano TEXT NOT NULL,
        valor REAL NOT NULL,
        vencimento TEXT NOT NULL,
        data_pagamento TEXT,
        status TEXT DEFAULT 'A Receber',
        FOREIGN KEY (id_aluno) REFERENCES alunos(id_aluno) ON DELETE CASCADE,
        UNIQUE(id_aluno, mes_ano)
    )''')
    conn.commit()
    conn.close()

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
criar_banco()
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
    conn = conectar()
    alunos = conn.execute("SELECT * FROM alunos ORDER BY nome").fetchall()
    conn.close()

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
                    conn = conectar()
                    cur = conn.cursor()
                    cur.execute('''INSERT INTO alunos VALUES (NULL,?,?,?,?,?,?,?,?)''',
                                (nome, resp, dt_mat, int(ano), valor_float, int(parcelas), mi_num, turno))
                    novo_id = cur.lastrowid
                    base = mi_num - 1
                    for i in range(int(parcelas)):
                        m = (base + i) % 12
                        ma = f"{LISTA_MESES[m]}/{ano}"
                        ve = f"10/{LISTA_MESES[m]}/{ano}"
                        cur.execute('''INSERT INTO mensalidades VALUES (NULL,?,?,?,?,NULL,'A Receber')''',
                                    (novo_id, ma, valor_float, ve))
                    conn.commit()
                    conn.close()
                    st.success("Aluno cadastrado! Vencimentos gerados para o dia 10 de cada mês.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.divider()
    st.subheader("Alunos Cadastrados")
    if alunos:
        for a in alunos:
            with st.expander(f"{a[1]} | {a[2]}"):
                st.write(f"📅 Matrícula: {a[3]} | Ano: {a[4]}")
                st.write(f"💰 Valor: {formatar_valor(a[5])} | Parcelas: {a[6]}")
                st.write(f"📆 Início: {NOMES_MESES[a[7]-1]} | Turno: {a[8]}")
                
                # Confirmação de exclusão
                if f"conf_excl_{a[0]}" not in st.session_state:
                    st.session_state[f"conf_excl_{a[0]}"] = False
                
                if not st.session_state[f"conf_excl_{a[0]}"]:
                    if st.button(f"🗑️ Excluir {a[1]}", key=f"btn_excl_{a[0]}"):
                        st.session_state[f"conf_excl_{a[0]}"] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Tem certeza que quer excluir este aluno e todas as suas mensalidades?")
                    col_nao, col_sim = st.columns(2)
                    if col_nao.button("❌ Não", key=f"nao_excl_{a[0]}"):
                        st.session_state[f"conf_excl_{a[0]}"] = False
                        st.rerun()
                    if col_sim.button("✅ Sim, excluir", key=f"sim_excl_{a[0]}"):
                        conn = conectar()
                        conn.execute("DELETE FROM alunos WHERE id_aluno=?", (a[0],))
                        conn.commit()
                        conn.close()
                        st.success("Aluno e mensalidades excluídos com sucesso!")
                        st.session_state[f"conf_excl_{a[0]}"] = False
                        st.rerun()
    else:
        st.info("Nenhum aluno cadastrado ainda.")

# ------------------------------
# TELA DE MENSALIDADES COM BAIXA RÁPIDA
# ------------------------------
elif menu == "Mensalidades":
    st.subheader("Controle de Mensalidades")
    conn = conectar()
    lista_alunos = conn.execute("SELECT id_aluno, nome FROM alunos ORDER BY nome").fetchall()
    conn.close()
    if not lista_alunos:
        st.warning("Cadastre um aluno primeiro!")
    else:
        id_escolhido = st.selectbox("Selecione o Aluno", lista_alunos, format_func=lambda x: x[1])[0]
        conn = conectar()
        mensais = conn.execute("SELECT * FROM mensalidades WHERE id_aluno=? ORDER BY mes_ano", (id_escolhido,)).fetchall()
        conn.close()
        hoje = datetime.now().strftime("%d/%m/%Y")

        st.divider()
        for m in mensais:
            status_exib = "Atrasada" if m[5] == "A Receber" and data_valida(m[4]) and datetime.strptime(m[4],"%d/%m/%Y") < datetime.strptime(hoje,"%d/%m/%Y") else m[5]
            cor = "🔴" if status_exib == "Atrasada" else ("🟢" if status_exib == "Quitada" else "🟡")
            with st.container(border=True):
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                col1.write(f"**{m[2]}**")
                col2.write(formatar_valor(m[3]))
                col3.write(f"Venc: {m[4]}")
                col4.write(f"{cor} {status_exib}")
                if m[5] != "Quitada" and col5.button(f"✅ Dar Baixa", key=f"baixar_{m[0]}"):
                    conn = conectar()
                    conn.execute('''UPDATE mensalidades SET status='Quitada', data_pagamento=? WHERE id_mensalidade=?''',
                                (hoje, m[0]))
                    conn.commit()
                    conn.close()
                    st.success("Baixa registrada com sucesso!")
                    st.rerun()
                if col6.button(f"Editar", key=f"edt_{m[0]}"):
                    st.session_state["editando"] = m
                if "editando" in st.session_state and st.session_state["editando"][0] == m[0]:
                    with st.form(f"form_mensal_{m[0]}", clear_on_submit=True):
                        novo_valor = st.text_input("Valor R$", value=str(m[3]).replace('.',','))
                        novo_venc = st.text_input("Vencimento", value=m[4])
                        novo_status = st.selectbox("Status", ["A Receber", "Quitada"], index=0 if m[5]=="A Receber" else 1)
                        dt_pg = st.text_input("Data Pagamento", value=m[6] if m[5]=="Quitada" else hoje)
                        if st.form_submit_button("Salvar Alteração"):
                            if not data_valida(novo_venc):
                                st.error("Data de vencimento inválida! Use dd/mm/aaaa")
                            else:
                                conn = conectar()
                                conn.execute('''UPDATE mensalidades SET valor=?, vencimento=?, data_pagamento=?, status=? WHERE id_mensalidade=?''',
                                            (float(novo_valor.replace(',','.')), novo_venc, dt_pg if novo_status=="Quitada" else None, novo_status, m[0]))
                                conn.commit()
                                conn.close()
                                st.success("Atualizado!")
                                del st.session_state["editando"]
                                st.rerun()

# ------------------------------
# RELATÓRIOS COM IMPRESSÃO
# ------------------------------
elif menu == "Relatórios":
    st.subheader("Relatórios")
    tipo = st.radio("Escolha", ["Todos", "A Receber", "Atrasadas", "Quitadas", "Por Período"], horizontal=True)
    
    conn = conectar()
    hoje = datetime.now().strftime("%d/%m/%Y")
    dados = None
    titulo_rel = ""

    if tipo == "Por Período":
        st.subheader("Filtrar por Período de Vencimento")
        col_d1, col_d2 = st.columns(2)
        dt_inicio = col_d1.text_input("Data Início (dd/mm/aaaa)", value="01/01/2026")
        dt_fim = col_d2.text_input("Data Fim (dd/mm/aaaa)", value=hoje)
        titulo_rel = f"Relatório de {dt_inicio} até {dt_fim}"
        
        if not data_valida(dt_inicio) or not data_valida(dt_fim):
            st.error("Use datas válidas no formato dd/mm/aaaa")
        else:
            dados = conn.execute('''
                SELECT a.nome AS Aluno, m.mes_ano AS "Mês/Ano", m.valor AS Valor, m.vencimento AS Vencimento, m.status AS Status 
                FROM mensalidades m 
                JOIN alunos a ON m.id_aluno = a.id_aluno 
                WHERE m.vencimento BETWEEN ? AND ?
                ORDER BY m.vencimento
            ''', (dt_inicio, dt_fim)).fetchall()

    elif tipo == "Todos":
        titulo_rel = "Relatório Geral de Mensalidades"
        dados = conn.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno ORDER BY m.vencimento").fetchall()
    elif tipo == "A Receber":
        titulo_rel = "Relatório - A Receber"
        dados = conn.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno WHERE m.status='A Receber' AND m.vencimento>=?", (hoje,)).fetchall()
    elif tipo == "Atrasadas":
        titulo_rel = "Relatório - Atrasadas"
        dados = conn.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno WHERE m.status='A Receber' AND m.vencimento<?", (hoje,)).fetchall()
    else: # Quitadas
        titulo_rel = "Relatório - Quitadas"
        dados = conn.execute("SELECT a.nome, m.mes_ano, m.valor, m.data_pagamento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno WHERE m.status='Quitada' ORDER BY m.vencimento").fetchall()

    if dados:
        # Converte para DataFrame para formatar e imprimir
        df = pd.DataFrame(dados, columns=["Aluno", "Mês/Ano", "Valor", "Data", "Status"])
        df["Valor"] = df["Valor"].apply(formatar_valor)
        total = sum(d[2] for d in dados)

        st.subheader(titulo_rel)
        st.dataframe(df, use_container_width=True)
        st.subheader(f"Total: {formatar_valor(total)}")

        # 🖨️ BOTÃO DE IMPRESSÃO
        st.divider()
        st.info("🖨️ Para imprimir: clique no botão abaixo → use Ctrl+P ou o ícone de impressora do navegador")
        if st.button("🖨️ Visualizar para Imprimir"):
            st.markdown(f'''
            <div style="text-align: center; font-family: Arial;">
                <h2>{titulo_rel}</h2>
                <p>Emitido em: {hoje}</p>
                <hr>
            </div>
            ''', unsafe_allow_html=True)
            st.table(df)
            st.markdown(f'''
            <div style="text-align: right; font-size: 18px; font-weight: bold; margin-top: 20px;">
                Total Geral: {formatar_valor(total)}
            </div>
            ''', unsafe_allow_html=True)
            st.success("✅ Agora aperte **Ctrl + P** ou clique no ícone de impressora do navegador para salvar em PDF ou imprimir!")

    elif tipo != "Por Período" or (tipo == "Por Período" and data_valida(dt_inicio) and data_valida(dt_fim)):
        st.info("Sem registros para esse filtro.")
    
    conn.close()