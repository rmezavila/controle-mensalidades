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
def criar_tabelas():
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
        FOREIGN KEY (id_aluno) REFERENCES alunos(id_aluno),
        UNIQUE(id_aluno, mes_ano)
    )''')
    conn.commit()
    conn.close()

criar_tabelas()

# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

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
    linhas = ""
    for _, linha in df.iterrows():
        linhas += "<tr>"
        for v in linha:
            val = str(v)
            if val in ["nan", "None"]: val = ""
            linhas += f"<td>{val}</td>"
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
            h1 {{ text-align: center; color: #2c3e50; text-align: center; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #000; padding: 8px; font-size: 13px; }}
            th {{ background: #2c3e50; color: white; }}
            tr:nth-child(even) {{ background: #f2f2f2; }}
            .total {{ margin-top: 20px; font-size: 18px; font-weight: bold; text-align: right; }}
            .data {{ text-align: right; color: #666; font-size: 12px; margin-bottom: 10px; }}
            .botao {{ margin: 20px 0; text-align: center; }}
            button {{ padding: 10px 25px; font-size: 16px; background: #2c3e50; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            @media print {{ .botao {{ display: none; }} th {{ background: #ccc !important; color: black !important; }} }}
        </style>
    </head>
    <body>
        <h1>{titulo}</h1>
        <p class="data">Emitido em: {data_emissao}</p>
        <table><tr>{cabecalho}</tr>{linhas}</table>
        {linha_total}
        <div class="botao"><button onclick="window.print()">🖨️ Imprimir</button></div>
        <script>window.onload=function(){{setTimeout(function(){{window.print()}},600);}};</script>
    </body>
    </html>"""
    return html

# ------------------------------
# MENU PRINCIPAL
# ------------------------------
menu = st.sidebar.selectbox(
    "📋 Menu Principal",
    ["Cadastrar Aluno", "Importar Alunos (CSV)", "Consultar Aluno", "Lançar Pagamento", "Lista de Alunos", "Relatórios", "Excluir Aluno"]
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
            resp = st.text_input("Responsável")
            dt_mat = st.date_input("📅 Data Matrícula", value=datetime.now(), format="DD/MM/YYYY")
            ano = st.number_input("Ano Letivo", min_value=2020, max_value=2030, value=datetime.now().year)
        with col2:
            valor = st.number_input("Valor Mensal (R$)", min_value=0.0, step=10.0)
            parcelas = st.number_input("Quantidade de Parcelas", min_value=1, max_value=12, value=1)
            mes_inic = st.selectbox("Mês Inicial", options=range(1,13), format_func=lambda x: NOMES_MESES[x-1])
            turno = st.selectbox("Turno", ["Manhã", "Tarde", "Noite", "Integral"])
            dia_venc = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=5)
        if st.form_submit_button("💾 Salvar"):
            if nome and resp:
                conn = conectar()
                cur = conn.cursor()
                cur.execute("INSERT INTO alunos VALUES (NULL,?,?,?,?,?,?,?,?)",
                    (nome, resp, data_br(dt_mat), ano, valor, parcelas, mes_inic, turno))
                id_aluno = cur.lastrowid
                ano_base = ano
                mes_atual = mes_inic
                for _ in range(parcelas):
                    mes_ano = f"{LISTA_MESES[mes_atual-1]}/{ano_base}"
                    try:
                        dt_venc = datetime(ano_base, mes_atual, dia_venc).strftime("%d/%m/%Y")
                    except:
                        dt_venc = f"01/{LISTA_MESES[mes_atual-1]}/{ano_base}"
                    cur.execute("INSERT INTO mensalidades VALUES (NULL,?,?,?,?,?,?)",
                        (id_aluno, mes_ano, valor, dt_venc, None, "A Receber"))
                    mes_atual += 1
                    if mes_atual > 12:
                        mes_atual = 1
                        ano_base += 1
                conn.commit()
                conn.close()
                st.success(f"✅ Aluno cadastrado! +{parcelas} mensalidades geradas!")
                st.rerun()
            else:
                st.error("Preencha Nome e Responsável!")

# ------------------------------
# ✅ 2. IMPORTAR ALUNOS POR ARQUIVO CSV
# ------------------------------
elif menu == "Importar Alunos (CSV)":
    st.subheader("📂 Importar Alunos de Arquivo CSV")
    st.info("💡 Baixe o arquivo do seu notebook em 'Lista de Alunos → Baixar CSV' e envie aqui!")
    
    arquivo = st.file_uploader("Escolha o arquivo .csv", type="csv")
    
    if arquivo:
        try:
            df = pd.read_csv(arquivo, sep=';', encoding='utf-8')
            st.success(f"✅ Arquivo carregado! Encontrados {len(df)} alunos!")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            if st.button("📥 Importar TODOS para o Sistema"):
                conn = conectar()
                cur = conn.cursor()
                contador = 0
                erros = []
                
                for _, linha in df.iterrows():
                    try:
                        nome = str(linha.get("Aluno", linha.get("nome", ""))).strip()
                        resp = str(linha.get("Responsável", linha.get("responsavel", ""))).strip()
                        dt_mat = str(linha.get("Matrícula", linha.get("data_matricula", ""))).strip()
                        ano = int(linha.get("Ano", linha.get("ano_letivo", datetime.now().year)))
                        valor = float(str(linha.get("Valor Mensal", linha.get("valor_mensal", 0))).replace("R$","").replace(",","."))
                        parcelas = int(linha.get("Parcelas", linha.get("qtd_parcelas", 1)))
                        turno = str(linha.get("Turno", linha.get("turno", "Manhã"))).strip()
                        mes_inic = 1
                        dia_venc = 5
                        
                        if nome:
                            cur.execute("INSERT INTO alunos VALUES (NULL,?,?,?,?,?,?,?,?)",
                                (nome, resp, dt_mat, ano, valor, parcelas, mes_inic, turno))
                            id_aluno = cur.lastrowid
                            ano_base = ano
                            mes_atual = mes_inic
                            for _ in range(parcelas):
                                mes_ano = f"{LISTA_MESES[mes_atual-1]}/{ano_base}"
                                try:
                                    dt_v = datetime(ano_base, mes_atual, dia_venc).strftime("%d/%m/%Y")
                                except:
                                    dt_v = f"01/{LISTA_MESES[mes_atual-1]}/{ano_base}"
                                cur.execute("INSERT INTO mensalidades VALUES (NULL,?,?,?,?,?,?)",
                                    (id_aluno, mes_ano, valor, dt_v, None, "A Receber"))
                                mes_atual += 1
                                if mes_atual > 12:
                                    mes_atual = 1
                                    ano_base += 1
                            contador += 1
                    except Exception as e:
                        erros.append(f"{nome}: {str(e)}")
                        continue
                
                conn.commit()
                conn.close()
                st.success(f"✅ {contador} alunos importados com SUCESSO!")
                if erros:
                    st.warning(f"⚠️ {len(erros)} alunos com erro: {', '.join(erros[:5])}...")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Erro ao ler arquivo: {str(e)}")

# ------------------------------
# 3. CONSULTAR ALUNO
# ------------------------------
elif menu == "Consultar Aluno":
    st.subheader("🔍 Consultar Aluno")
    conn = conectar()
    alunos_df = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()
    if not alunos_df.empty:
        id_esc = st.selectbox("Selecione o Aluno", options=alunos_df["id_aluno"],
            format_func=lambda x: alunos_df[alunos_df["id_aluno"]==x]["nome"].values[0])
        conn = conectar()
        dados = pd.read_sql("SELECT * FROM alunos WHERE id_aluno=?", conn, params=(id_esc,))
        mensal = pd.read_sql("SELECT mes_ano, valor, vencimento, data_pagamento, status FROM mensalidades WHERE id_aluno=? ORDER BY mes_ano", conn, params=(id_esc,))
        conn.close()
        st.write("📋 Dados Cadastrais:")
        st.dataframe(dados, use_container_width=True, hide_index=True)
        st.write("💳 Mensalidades:")
        if not mensal.empty:
            mensal["valor"] = mensal["valor"].apply(lambda x: formatar_valor(x))
            st.dataframe(mensal.style.map(cor_status, subset=["status"]), use_container_width=True, hide_index=True)
        else:
            st.info("Sem mensalidades.")
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 4. LANÇAR PAGAMENTO
# ------------------------------
elif menu == "Lançar Pagamento":
    st.subheader("💳 Lançar Pagamento")
    conn = conectar()
    alunos_df = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()
    if not alunos_df.empty:
        id_esc = st.selectbox("Aluno", options=alunos_df["id_aluno"],
            format_func=lambda x: alunos_df[alunos_df["id_aluno"]==x]["nome"].values[0])
        conn = conectar()
        mensal = pd.read_sql("SELECT * FROM mensalidades WHERE id_aluno=? ORDER BY mes_ano", conn, params=(id_esc,))
        conn.close()
        if not mensal.empty:
            mensal["valor"] = mensal["valor"].apply(lambda x: formatar_valor(x))
            st.dataframe(mensal.style.map(cor_status, subset=["status"]), use_container_width=True, hide_index=True)
            with st.form("pagto"):
                id_m = st.selectbox("Mês/Ano", options=mensal["id_mensalidade"],
                    format_func=lambda x: mensal[mensal["id_mensalidade"]==x]["mes_ano"].values[0])
                status = st.selectbox("Status", ["A Receber", "Quitada", "Atrasada"])
                dt_pag = st.date_input("📅 Data Pagamento", value=None, format="DD/MM/YYYY")
                if st.form_submit_button("💾 Salvar"):
                    dt_final = data_br(dt_pag) if dt_pag else (datetime.now().strftime("%d/%m/%Y") if status=="Quitada" else None)
                    conn = conectar()
                    conn.cursor().execute("UPDATE mensalidades SET status=?, data_pagamento=? WHERE id_mensalidade=?", (status, dt_final, id_m))
                    conn.commit()
                    conn.close()
                    st.success("✅ Salvo!")
                    st.rerun()
        else:
            st.info("Sem mensalidades.")
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 5. LISTA DE ALUNOS
# ------------------------------
elif menu == "Lista de Alunos":
    st.subheader("📋 Lista de Alunos — Ordem Alfabética")
    conn = conectar()
    df = pd.read_sql("SELECT nome AS [Aluno], responsavel AS [Responsável], data_matricula AS [Matrícula], ano_letivo AS [Ano], valor_mensal AS [Valor Mensal], qtd_parcelas AS [Parcelas], turno AS Turno FROM alunos ORDER BY nome", conn)
    conn.close()
    if not df.empty:
        df_csv = df.copy()
        df_csv["Valor Mensal"] = df_csv["Valor Mensal"].apply(lambda x: f"{x:.2f}".replace(".",","))
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.subheader(f"👥 Total: {len(df)} alunos")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🖨️ Imprimir Lista"):
                html = gerar_html_impressao("Lista de Alunos", df)
                st.download_button("📄 Abrir para Impressão", html, "lista_alunos.html", "text/html")
        with col2:
            csv = df_csv.to_csv(index=False, sep=';', encoding='utf-8')
            st.download_button("📥 Baixar CSV (para importar)", csv, "alunos_para_importar.csv", "text/csv")
    else:
        st.info("Nenhum aluno cadastrado.")

# ------------------------------
# 6. RELATÓRIOS
# ------------------------------
elif menu == "Relatórios":
    st.subheader("📊 Relatórios")
    tipo = st.radio("Tipo", ["Todos por Vencimento", "A Receber", "Atrasadas", "Quitadas"])
    st.subheader("📅 Período")
    col1, col2 = st.columns(2)
    with col1:
        dti = st.date_input("De", value=datetime(datetime.now().year,1,1), format="DD/MM/YYYY")
    with col2:
        dtf = st.date_input("Até", value=datetime.now(), format="DD/MM/YYYY")
    
    dti_sql = f"{dti.year}-{dti.month:02d}-{dti.day:02d}"
    dtf_sql = f"{dtf.year}-{dtf.month:02d}-{dtf.day:02d}"

    filtro = ""
    if tipo == "A Receber": filtro = " AND m.status = 'A Receber'"
    elif tipo == "Atrasadas": filtro = " AND m.status = 'Atrasada'"
    elif tipo == "Quitadas": filtro = " AND m.status = 'Quitada'"

    sql = f"""
        SELECT a.nome AS [Aluno], a.responsavel AS [Responsável], m.mes_ano AS [Mês/Ano],
               m.vencimento AS [Vencimento], m.valor AS Valor, m.data_pagamento AS [Pagamento], m.status AS Status
        FROM alunos a JOIN mensalidades m ON a.id_aluno = m.id_aluno
        WHERE LENGTH(m.vencimento)=10
          AND DATE(SUBSTR(m.vencimento,7,4)||'-'||SUBSTR(m.vencimento,4,2)||'-'||SUBSTR(m.vencimento,1,2))
              BETWEEN DATE(?) AND DATE(?)
          {filtro}
        ORDER BY m.vencimento
    """
    conn = conectar()
    rel = pd.read_sql(sql, conn, params=(dti_sql, dtf_sql))
    conn.close()

    if not rel.empty:
        rel["Valor"] = rel["Valor"].apply(lambda x: f"{x:.2f}".replace(".",","))
        total = rel["Valor"].str.replace(",",".").astype(float).sum()
        st.dataframe(rel.style.map(cor_status, subset=["Status"]), use_container_width=True, hide_index=True)
        st.subheader(f"💰 Total: {formatar_valor(total)}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🖨️ Imprimir Relatório"):
                html = gerar_html_impressao(f"Relatório: {tipo}", rel, f"Total: {formatar_valor(total)}")
                st.download_button("📄 Abrir para Impressão", html, f"rel_{tipo}.html", "text/html")
        with col2:
            csv = rel.to_csv(index=False, sep=';', encoding='utf-8')
            st.download_button("📥 Baixar CSV", csv, f"relatorio_{tipo}.csv", "text/csv")
    else:
        st.info("Nenhum registro no período.")

# ------------------------------
# 7. EXCLUIR ALUNO
# ------------------------------
elif menu == "Excluir Aluno":
    st.subheader("🗑️ Excluir Aluno")
    st.warning("⚠️ Essa ação apaga o aluno e TODAS as mensalidades!")
    conn = conectar()
    alunos_df = pd.read_sql("SELECT id_aluno, nome FROM alunos ORDER BY nome", conn)
    conn.close()
    if not alunos_df.empty:
        id_esc = st.selectbox("Aluno", options=alunos_df["id_aluno"],
            format_func=lambda x: alunos_df[alunos_df["id_aluno"]==x]["nome"].values[0])
        if st.checkbox("Confirmo que desejo EXCLUIR") and st.button("🗑️ Excluir Agora"):
            conn = conectar()
            conn.cursor().execute("DELETE FROM mensalidades WHERE id_aluno=?", (id_esc,))
            conn.cursor().execute("DELETE FROM alunos WHERE id_aluno=?", (id_esc,))
            conn.commit()
            conn.close()
            st.success("✅ Aluno excluído!")
            st.rerun()
    else:
        st.info("Nenhum aluno cadastrado.")
