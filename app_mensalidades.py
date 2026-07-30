import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import os
import shutil

# ------------------------------
# CONFIGURAÇÃO
# ------------------------------
st.set_page_config(page_title="Controle de Mensalidades", layout="wide")
st.title("📚 Controle de Mensalidades")

ARQ_DB = 'controle_mensalidades_novo.db'

# ------------------------------
# BANCO DE DADOS + CORREÇÃO DE DADOS ANTIGOS
# ------------------------------
def conectar():
    return sqlite3.connect(ARQ_DB, timeout=5)

def formatar_data_fixa(data_str):
    """Transforma QUALQUER data em dd/mm/aaaa"""
    if not data_str or str(data_str).strip() == "" or str(data_str) == "None":
        return ""
    s = str(data_str).strip().replace("/", "").replace("-", "").replace(".", "")
    try:
        if len(s) == 8 and s.isdigit():
            return f"{s[0:2]}/{s[2:4]}/{s[4:8]}"
        return datetime.strptime(s, "%d%m%Y").strftime("%d/%m/%Y")
    except:
        try:
            return datetime.strptime(s, "%d/%m/%Y").strftime("%d/%m/%Y")
        except:
            return data_str

def corrigir_dados_banco():
    """Correção única: formata todas as datas que já estão salvas"""
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT id_mensalidade, vencimento, data_pagamento FROM mensalidades")
    todos = cur.fetchall()
    for id_m, ven, pag in todos:
        ven_novo = formatar_data_fixa(ven)
        pag_novo = formatar_data_fixa(pag)
        cur.execute("UPDATE mensalidades SET vencimento = ?, data_pagamento = ? WHERE id_mensalidade = ?", (ven_novo, pag_novo, id_m))
    conn.commit()
    conn.close()

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

criar_banco()
corrigir_dados_banco()

# ------------------------------
# BACKUP
# ------------------------------
def fazer_backup():
    try:
        pasta = "BACKUPS"
        if not os.path.exists(pasta): os.makedirs(pasta)
        dh = datetime.now().strftime("%Y%m%d_%H%M")
        shutil.copy2(ARQ_DB, os.path.join(pasta, f"backup_{dh}.db"))
        arquivos = sorted([os.path.join(pasta, f) for f in os.listdir(pasta) if f.startswith("backup_")], key=os.path.getmtime)
        if len(arquivos) > 10: os.remove(arquivos[0])
    except: pass

# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

def formatar_valor_df(valor):
    return f"{valor:.2f}".replace('.', ',')

def data_valida(data):
    try: datetime.strptime(data, "%d/%m/%Y"); return True
    except: return False

NOMES_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LISTA_MESES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

fazer_backup()

# ------------------------------
# FUNÇÃO DE CORES
# ------------------------------
def cor_status(valor):
    if valor == "Atrasada":
        return 'background-color: #ffd6d6'
    elif valor == "Quitada":
        return 'background-color: #d6ffd6'
    elif valor == "A Receber":
        return 'background-color: #ffffd6'
    return ''

# ------------------------------
# MENU
# ------------------------------
menu = st.sidebar.selectbox(
    "📋 Menu Principal",
    ["Cadastrar Aluno", "Consultar Aluno", "Lançar Pagamento", "Lista de Alunos", "Relatórios", "Excluir Aluno"]
)

# ------------------------------
# 1. CADASTRAR ALUNO
# ------------------------------
if menu == "Cadastrar Aluno":
    st.subheader("➕ Cadastrar Novo Aluno")
    with st.form("form_aluno", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Aluno")
            responsavel = st.text_input("Responsável")
            data_matricula = st.text_input("Data Matrícula (dd/mm/aaaa)", value=datetime.now().strftime("%d/%m/%Y"))
            ano_letivo = st.number_input("Ano Letivo", min_value=2020, max_value=2030, value=datetime.now().year)
        with col2:
            valor_mensal = st.number_input("Valor Mensal (R$)", min_value=0.0, format="%.2f")
            qtd_parcelas = st.number_input("Quantidade de Parcelas", min_value=1, max_value=12, value=12)
            mes_inicial = st.selectbox("Mês Inicial", options=range(1,13), format_func=lambda x: NOMES_MESES[x-1])
            turno = st.selectbox("Turno", ["Manhã", "Tarde", "Noite", "Integral"])
            dia_vencimento = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=5)
        
        if st.form_submit_button("💾 Salvar Aluno"):
            if not all([nome, responsavel, data_matricula, ano_letivo, valor_mensal, qtd_parcelas, mes_inicial, turno]):
                st.error("Preencha todos os campos!")
            elif not data_valida(data_matricula):
                st.error("Data inválida! Use dd/mm/aaaa")
            else:
                conn = conectar()
                cur = conn.cursor()
                cur.execute('''
                INSERT INTO alunos (nome, responsavel, data_matricula, ano_letivo, valor_mensal, qtd_parcelas, mes_inicial, turno)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (nome, responsavel, data_matricula, ano_letivo, valor_mensal, qtd_parcelas, mes_inicial, turno))
                id_novo = cur.lastrowid

                ano_base = ano_letivo
                mes_atual = mes_inicial
                for _ in range(qtd_parcelas):
                    mes_ano = f"{LISTA_MESES[mes_atual-1]}/{ano_base}"
                    try:
                        data_venc = datetime(ano_base, mes_atual, dia_vencimento).strftime("%d/%m/%Y")
                    except:
                        data_venc = datetime(ano_base, mes_atual, 1).strftime("%d/%m/%Y")
                    cur.execute('''
                    INSERT INTO mensalidades (id_aluno, mes_ano, valor, vencimento)
                    VALUES (?, ?, ?, ?)
                    ''', (id_novo, mes_ano, valor_mensal, data_venc))
                    mes_atual += 1
                    if mes_atual > 12:
                        mes_atual = 1
                        ano_base += 1

                conn.commit()
                conn.close()
                fazer_backup()
                st.success(f"Aluno cadastrado + {qtd_parcelas} mensalidades geradas!")
                st.rerun()

# ------------------------------
# 2. CONSULTAR ALUNO
# ------------------------------
elif menu == "Consultar Aluno":
    st.subheader("🔍 Consultar Dados do Aluno")
    conn = conectar()
    alunos = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()

    if not alunos.empty:
        id_aluno = st.selectbox("Selecione o Aluno", options=alunos['id_aluno'], format_func=lambda x: alunos[alunos['id_aluno']==x]['nome'].values[0])
        if id_aluno:
            conn = conectar()
            dados_aluno = pd.read_sql("SELECT * FROM alunos WHERE id_aluno = ?", conn, params=(id_aluno,))
            mensalidades = pd.read_sql("""
                SELECT mes_ano, valor, vencimento AS "Data de Vencimento", 
                       data_pagamento AS "Data de Pagamento", status 
                FROM mensalidades WHERE id_aluno = ? ORDER BY mes_ano
            """, conn, params=(id_aluno,))
            conn.close()

            if not mensalidades.empty:
                mensalidades["valor"] = mensalidades["valor"].apply(formatar_valor_df)
                mensalidades["Data de Vencimento"] = mensalidades["Data de Vencimento"].apply(formatar_data_fixa)
                mensalidades["Data de Pagamento"] = mensalidades["Data de Pagamento"].apply(formatar_data_fixa)

            st.write("📋 Dados Cadastrais:")
            st.dataframe(dados_aluno, use_container_width=True)

            st.write("💳 Histórico de Mensalidades:")
            if not mensalidades.empty:
                styled = mensalidades.style.map(cor_status, subset=["status"])
                st.dataframe(styled, use_container_width=True)
            else:
                st.info("Nenhuma mensalidade gerada.")
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 3. LANÇAR PAGAMENTO (CORREÇÃO FINAL DA DATA!)
# ------------------------------
elif menu == "Lançar Pagamento":
    st.subheader("💳 Lançar Pagamento e Atualizar Status")
    conn = conectar()
    alunos = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()

    if not alunos.empty:
        id_aluno = st.selectbox("Aluno", options=alunos['id_aluno'], format_func=lambda x: alunos[alunos['id_aluno']==x]['nome'].values[0])
        if id_aluno:
            conn = conectar()
            mensal = pd.read_sql("""
                SELECT id_mensalidade, mes_ano, valor, vencimento AS "Data de Vencimento", 
                       data_pagamento AS "Data de Pagamento", status 
                FROM mensalidades WHERE id_aluno = ? ORDER BY mes_ano
            """, conn, params=(id_aluno,))
            conn.close()

            if not mensal.empty:
                mensal["valor"] = mensal["valor"].apply(formatar_valor_df)
                mensal["Data de Vencimento"] = mensal["Data de Vencimento"].apply(formatar_data_fixa)
                mensal["Data de Pagamento"] = mensal["Data de Pagamento"].apply(formatar_data_fixa)
                st.dataframe(
                    mensal.style.map(cor_status, subset=["status"]),
                    use_container_width=True
                )
                with st.form("form_pagamento", clear_on_submit=False):
                    id_mensal = st.selectbox(
                        "Mensalidade", 
                        options=mensal['id_mensalidade'], 
                        format_func=lambda x: f"{mensal[mensal['id_mensalidade']==x]['mes_ano'].values[0]} - R$ {mensal[mensal['id_mensalidade']==x]['valor'].values[0]}"
                    )
                    novo_status = st.selectbox("Status", ["A Receber", "Quitada", "Atrasada"])
                    
                    # ✅ MOSTRA A DATA JÁ SALVA, SE TIVER; SE NÃO, SUGERE HOJE SÓ PARA QUITADA
                    data_atual = mensal[mensal['id_mensalidade']==id_mensal]['Data de Pagamento'].values[0]
                    if data_atual in [None, "", "None"]:
                        data_pag = st.text_input(
                            "Data Pagamento (dd/mm/aaaa)", 
                            value=datetime.now().strftime("%d/%m/%Y") if novo_status == "Quitada" else ""
                        )
                    else:
                        data_pag = st.text_input(
                            "Data Pagamento (dd/mm/aaaa)", 
                            value=data_atual
                        )

                    if st.form_submit_button("✅ Salvar Alteração"):
                        # ✅ USA EXATAMENTE O QUE VOCÊ DIGITOU; SÓ HOJE SE ESTIVER VAZIO E QUITADA
                        if data_pag.strip() == "" and novo_status == "Quitada":
                            data_final = datetime.now().strftime("%d/%m/%Y")
                        elif data_pag.strip() == "":
                            data_final = None
                        else:
                            data_final = data_pag.strip()

                        conn = conectar()
                        cur = conn.cursor()
                        cur.execute('''
                        UPDATE mensalidades SET status = ?, data_pagamento = ? WHERE id_mensalidade = ?
                        ''', (novo_status, data_final, id_mensal))
                        conn.commit()
                        conn.close()
                        fazer_backup()
                        st.success("Pagamento lançado com sucesso! A data informada foi mantida.")
                        st.rerun()
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 4. LISTA DE ALUNOS
# ------------------------------
elif menu == "Lista de Alunos":
    st.subheader("📋 Todos os Alunos Cadastrados")
    conn = conectar()
    df = pd.read_sql("SELECT * FROM alunos ORDER BY nome", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Sem alunos cadastrados.")

# ------------------------------
# 5. RELATÓRIOS
# ------------------------------
elif menu == "Relatórios":
    st.subheader("📊 Relatórios")
    tipo = st.radio("Escolha o relatório", ["Todos os Lançamentos", "A Receber", "Atrasadas", "Quitadas", "Por Aluno"])
    
    st.subheader("📅 Filtrar por Período de Vencimento")
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.text_input("Data Inicial (dd/mm/aaaa)", value="01/01/2026")
    with col2:
        data_fim = st.text_input("Data Final (dd/mm/aaaa)", value=datetime.now().strftime("%d/%m/%Y"))

    if not data_valida(data_inicio) or not data_valida(data_fim):
        st.error("Digite as datas no formato dd/mm/aaaa!")
    else:
        conn = conectar()
        base_sql = '''
            SELECT a.nome, a.responsavel, m.mes_ano, m.valor, 
                   m.vencimento AS "Data de Vencimento", 
                   m.data_pagamento AS "Data de Pagamento", m.status
            FROM alunos a JOIN mensalidades m ON a.id_aluno = m.id_aluno
            WHERE DATE(SUBSTR(m.vencimento,7,4) || '-' || SUBSTR(m.vencimento,4,2) || '-' || SUBSTR(m.vencimento,1,2)) 
                  BETWEEN DATE(?) AND DATE(?)
        '''
        params = [datetime.strptime(data_inicio, "%d/%m/%Y").strftime("%Y-%m-%d"),
                  datetime.strptime(data_fim, "%d/%m/%Y").strftime("%Y-%m-%d")]

        if tipo == "Todos os Lançamentos":
            rel = pd.read_sql(base_sql + " ORDER BY a.nome, m.vencimento", conn, params=params)
        elif tipo == "A Receber":
            rel = pd.read_sql(base_sql + " AND m.status = 'A Receber' ORDER BY m.vencimento", conn, params=params)
        elif tipo == "Atrasadas":
            rel = pd.read_sql(base_sql + " AND m.status = 'Atrasada' ORDER BY m.vencimento", conn, params=params)
        elif tipo == "Quitadas":
            rel = pd.read_sql(base_sql + " AND m.status = 'Quitada' ORDER BY m.data_pagamento", conn, params=params)
        else:
            lista_alunos = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
            id_escolhido = st.selectbox("Selecione o Aluno", options=lista_alunos['id_aluno'], format_func=lambda x: lista_alunos[lista_alunos['id_aluno']==x]['nome'].values[0])
            rel = pd.read_sql(base_sql + " AND a.id_aluno = ? ORDER BY m.vencimento", conn, params=params + [id_escolhido])
        conn.close()

        if not rel.empty:
            total_geral = rel["valor"].sum()
            rel["valor"] = rel["valor"].apply(formatar_valor_df)
            rel["Data de Vencimento"] = rel["Data de Vencimento"].apply(formatar_data_fixa)
            rel["Data de Pagamento"] = rel["Data de Pagamento"].apply(formatar_data_fixa)

            st.dataframe(
                rel.style.map(cor_status, subset=["status"]),
                use_container_width=True
            )
            st.subheader(f"💰 Valor Total do Período: {formatar_valor(total_geral)}")

            csv = rel.to_csv(index=False, sep=';', encoding='utf-8')
            st.download_button("📥 Baixar Relatório em CSV", csv, f"relatorio_{tipo}_{data_inicio.replace('/','-')}_a_{data_fim.replace('/','-')}.csv", "text/csv")
        else:
            st.info("Nenhum registro encontrado nesse período.")

# ------------------------------
# 6. EXCLUIR ALUNO
# ------------------------------
elif menu == "Excluir Aluno":
    st.subheader("🗑️ Excluir Aluno e Todos os Dados")
    st.warning("⚠️ ATENÇÃO: Essa ação apaga o aluno e todas as mensalidades para sempre! Não tem como desfazer.")
    
    conn = conectar()
    alunos = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()

    if not alunos.empty:
        id_aluno = st.selectbox("Selecione o Aluno para excluir", options=alunos['id_aluno'], format_func=lambda x: alunos[alunos['id_aluno']==x]['nome'].values[0])
        confirmar = st.checkbox("Eu confiro que quero apagar esse aluno e todos os seus registros")
        
        if confirmar and st.button("🗑️ Confirmar Exclusão"):
            conn = conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM alunos WHERE id_aluno = ?", (id_aluno,))
            conn.commit()
            conn.close()
            fazer_backup()
            st.success("Aluno excluído com sucesso!")
            st.rerun()