import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# ------------------------------
# CONFIGURAÇÃO
# ------------------------------
st.set_page_config(page_title="Controle de Mensalidades", layout="wide")
st.title("📚 Controle de Mensalidades")

ARQ_DB = 'mensalidades.db'

# ------------------------------
# CONEXÃO COM BANCO
# ------------------------------
def conectar():
    return sqlite3.connect(ARQ_DB, timeout=10)

# ------------------------------
# CRIAR TABELAS
# ------------------------------
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

# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

def formatar_valor_df(valor):
    return f"{valor:.2f}".replace('.', ',')

def data_br(data):
    return data.strftime("%d/%m/%Y") if data else ""

NOMES_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LISTA_MESES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

def cor_status(valor):
    if valor == "Atrasada": return 'background-color: #ffd6d6'
    elif valor == "Quitada": return 'background-color: #d6ffd6'
    elif valor == "A Receber": return 'background-color: #ffffd6'
    return ''

def gerar_html_impressao(titulo, df, total=""):
    """Gera página formatada que abre direto na impressora"""
    linhas = ""
    for _, row in df.iterrows():
        linhas += "<tr>"
        for v in row:
            valor = str(v)
            if valor == "nan":
                valor = ""
            linhas += f"<td>{valor}</td>"
        linhas += "</tr>"

    cabecalho = "".join(f"<th>{c}</th>" for c in df.columns)
    data_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")
    linha_total = f"<p class='total'>{total}</p>" if total else ""

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{titulo}</title>
        <style>
            body {{ font-family: Arial; padding: 20px; }}
            h1 {{ text-align: center; color: #2c3e50; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #000; padding: 8px; text-align: left; font-size: 13px; }}
            th {{ background: #2c3e50; color: white; }}
            tr:nth-child(even) {{ background: #f2f2f2; }}
            .total {{ margin-top: 20px; font-size: 18px; font-weight: bold; text-align: right; }}
            .data {{ text-align: right; color: #666; font-size: 12px; margin-bottom: 10px; }}
            .botao {{ margin: 20px 0; text-align: center; }}
            button {{ padding: 10px 25px; font-size: 16px; cursor: pointer; background: #2c3e50; color: white; border: none; border-radius: 5px; }}
            @media print {{
                .botao {{ display: none; }}
                th {{ background: #ccc !important; color: black !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body>
        <h1>{titulo}</h1>
        <p class="data">Emitido em: {data_emissao}</p>
        <table>
            <tr>{cabecalho}</tr>
            {linhas}
        </table>
        {linha_total}
        <div class="botao">
            <button onclick="window.print()">🖨️ Clique Aqui para Imprimir</button>
        </div>
        <script>window.onload=function(){{setTimeout(function(){{window.print()}},500);}};</script>
    </body>
    </html>
    """
    return html
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
            data_matricula = st.date_input("📅 Data Matrícula", value=datetime.now(), format="DD/MM/YYYY")
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
            else:
                conn = conectar()
                cur = conn.cursor()
                cur.execute('INSERT INTO alunos VALUES (NULL,?,?,?,?,?,?,?,?)',
                            (nome, responsavel, data_br(data_matricula), ano_letivo, valor_mensal, qtd_parcelas, mes_inicial, turno))
                id_novo = cur.lastrowid

                ano_base = ano_letivo
                mes_atual = mes_inicial
                for _ in range(qtd_parcelas):
                    mes_ano = f"{LISTA_MESES[mes_atual-1]}/{ano_base}"
                    try:
                        data_venc = datetime(ano_base, mes_atual, dia_vencimento).strftime("%d/%m/%Y")
                    except:
                        data_venc = datetime(ano_base, mes_atual, 1).strftime("%d/%m/%Y")
                    cur.execute('INSERT INTO mensalidades VALUES (NULL,?,?,?,?,?, "A Receber")',
                                (id_novo, mes_ano, valor_mensal, data_venc, None))
                    mes_atual += 1
                    if mes_atual > 12:
                        mes_atual = 1
                        ano_base += 1

                conn.commit()
                conn.close()
                st.success(f"✅ Aluno cadastrado + {qtd_parcelas} mensalidades geradas!")
                st.rerun()

# ------------------------------
# 2. CONSULTAR ALUNO
# ------------------------------
elif menu == "Consultar Aluno":
    st.subheader("🔍 Consultar Aluno")
    conn = conectar()
    alunos = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()
    if not alunos.empty:
        id_aluno = st.selectbox("Selecione o Aluno", options=alunos['id_aluno'], format_func=lambda x: alunos[alunos['id_aluno']==x]['nome'].values[0])
        conn = conectar()
        dados = pd.read_sql("SELECT * FROM alunos WHERE id_aluno=?", conn, params=(id_aluno,))
        mensal = pd.read_sql("SELECT mes_ano, valor, vencimento, data_pagamento, status FROM mensalidades WHERE id_aluno=? ORDER BY mes_ano", conn, params=(id_aluno,))
        conn.close()
        st.write("📋 Dados Cadastrais:")
        st.dataframe(dados, use_container_width=True)
        st.write("💳 Mensalidades:")
        if not mensal.empty:
            mensal["valor"] = mensal["valor"].apply(formatar_valor_df)
            st.dataframe(mensal.style.map(cor_status, subset=["status"]), use_container_width=True)
        else:
            st.info("Nenhuma mensalidade.")
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 3. LANÇAR PAGAMENTO
# ------------------------------
elif menu == "Lançar Pagamento":
    st.subheader("💳 Lançar Pagamento")
    conn = conectar()
    alunos = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()
    if not alunos.empty:
        id_aluno = st.selectbox("Aluno", options=alunos['id_aluno'], format_func=lambda x: alunos[alunos['id_aluno']==x]['nome'].values[0])
        conn = conectar()
        mensal = pd.read_sql("SELECT * FROM mensalidades WHERE id_aluno=? ORDER BY mes_ano", conn, params=(id_aluno,))
        conn.close()
        if not mensal.empty:
            mensal["valor"] = mensal["valor"].apply(formatar_valor_df)
            st.dataframe(mensal.style.map(cor_status, subset=["status"]), use_container_width=True)
            with st.form("pagamento"):
                id_m = st.selectbox("Mensalidade", options=mensal['id_mensalidade'],
                    format_func=lambda x: f"{mensal[mensal['id_mensalidade']==x]['mes_ano'].values[0]}")
                status = st.selectbox("Status", ["A Receber", "Quitada", "Atrasada"])
                data_pag = st.date_input("📅 Data Pagamento", value=None, format="DD/MM/YYYY")
                
                if st.form_submit_button("✅ Salvar"):
                    dt = data_br(data_pag) if data_pag else (datetime.now().strftime("%d/%m/%Y") if status=="Quitada" else None)
                    conn = conectar()
                    conn.cursor().execute("UPDATE mensalidades SET status=?, data_pagamento=? WHERE id_mensalidade=?", (status, dt, id_m))
                    conn.commit()
                    conn.close()
                    st.success("✅ Salvo com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 4. LISTA DE ALUNOS + IMPRIMIR
# ------------------------------
elif menu == "Lista de Alunos":
    st.subheader("📋 Lista de Alunos — Ordem Alfabética")
    conn = conectar()
    df = pd.read_sql("SELECT nome AS [Aluno], responsavel AS [Responsável], data_matricula AS [Matrícula], ano_letivo AS [Ano], valor_mensal AS [Valor Mensal], turno AS Turno FROM alunos ORDER BY nome ASC", conn)
    conn.close()
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.subheader(f"👥 Total de Alunos: {len(df)}")
        
        # 🖨️ BOTÃO DE IMPRIMIR
        if st.button("🖨️ Imprimir Lista"):
            html = gerar_html_impressao("Lista de Alunos", df)
            st.download_button("📄 Baixar para Impressão", html, "lista_alunos.html", "text/html")
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 5. RELATÓRIOS COMPLETOS + IMPRIMIR
# ------------------------------
elif menu == "Relatórios":
    st.subheader("📊 Relatórios")
    
    tipo = st.radio("Escolha o Relatório", [
        "Todos os Lançamentos por Vencimento",
        "A Receber",
        "Atrasadas",
        "Quitadas"
    ])
    
    st.subheader("📅 Filtrar por Período de Vencimento")
    col1, col2 = st.columns(2)
    with col1:
        data_ini = st.date_input("Data Inicial", value=datetime(datetime.now().year, 1, 1), format="DD/MM/YYYY")
    with col2:
        data_fim = st.date_input("Data Final", value=datetime.now(), format="DD/MM/YYYY")
    
    dt_ini_sql = data_br(data_ini)[6:10] + "-" + data_br(data_ini)[3:5] + "-" + data_br(data_ini)[0:2]
    dt_fim_sql = data_br(data_fim)[6:10] + "-" + data_br(data_fim)[3:5] + "-" + data_br(data_fim)[0:2]

    sql_base = """
        SELECT a.nome AS [Aluno], a.responsavel AS [Responsável],
               m.mes_ano AS [Mês/Ano], m.vencimento AS [Vencimento],
               m.valor AS Valor, m.data_pagamento AS [Pagamento], m.status AS Status
        FROM alunos a
        JOIN mensalidades m ON a.id_aluno = m.id_aluno
        WHERE LENGTH(m.vencimento) = 10
          AND DATE(SUBSTR(m.vencimento,7,4) || '-' || SUBSTR(m.vencimento,4,2) || '-' || SUBSTR(m.vencimento,1,2))
              BETWEEN DATE(?) AND DATE(?)
    """
    params = [dt_ini_sql, dt_fim_sql]

    if tipo == "A Receber":
        sql_base += " AND m.status = 'A Receber' ORDER BY m.vencimento ASC"
    elif tipo == "Atrasadas":
        sql_base += " AND m.status = 'Atrasada' ORDER BY m.vencimento ASC"
    elif tipo == "Quitadas":
        sql_base += " AND m.status = 'Quitada' ORDER BY m.vencimento ASC"
    else:
        sql_base += " ORDER BY m.vencimento ASC"

    conn = conectar()
    rel = pd.read_sql(sql_base, conn, params=params)
    conn.close()

    if not rel.empty:
        rel["Valor"] = rel["Valor"].apply(formatar_valor_df)
        total = rel["Valor"].str.replace(',', '.').astype(float).sum()
        st.dataframe(rel.style.map(cor_status, subset=["Status"]), use_container_width=True, hide_index=True)
        st.subheader(f"💰 Valor Total do Período: {formatar_valor(total)}")

        col_imp, col_down = st.columns(2)
        with col_imp:
            if st.button("🖨️ Imprimir Relatório"):
                html = gerar_html_impressao(f"Relatório: {tipo}", rel, f"Valor Total: {formatar_valor(total)}")
                st.download_button("📄 Abrir para Impressão", html, f"relatorio_{tipo.replace(' ','_')}.html", "text/html")
        with col_down:
            csv = rel.to_csv(index=False, sep=';', encoding='utf-8')
            st.download_button("📥 Baixar em CSV", csv, f"relatorio_{tipo.replace(' ','_')}.csv", "text/csv")
    else:
        st.info("Nenhum registro encontrado no período selecionado.")

# ------------------------------
# 6. EXCLUIR ALUNO
# ------------------------------
elif menu == "Excluir Aluno":
    st.subheader("🗑️ Excluir Aluno")
    st.warning("⚠️ Apaga o aluno e todas as mensalidades!")
    conn = conectar()
    alunos = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()
    if not alunos.empty:
        id_aluno = st.selectbox("Aluno", options=alunos['id_aluno'], format_func=lambda x: alunos[alunos['id_aluno']==x]['nome'].values[0])
        if st.checkbox("Confirmo a exclusão") and st.button("🗑️ Excluir"):
            conn = conectar()
            conn.cursor().execute("DELETE FROM alunos WHERE id_aluno=?", (id_aluno,))
            conn.commit()
            conn.close()
            st.success("✅ Aluno excluído!")
            st.rerun()
    else:
        st.info("Nenhum aluno cadastrado.")
