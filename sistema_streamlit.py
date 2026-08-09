import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
from io import BytesIO
import unicodedata

# ------------------------------
# ARQUIVOS DE DADOS
# ------------------------------
ARQ_ALUNOS = "alunos.csv"
ARQ_MENSAL = "mensalidades.csv"

def inicializar_arquivos():
    if not os.path.exists(ARQ_ALUNOS) or os.path.getsize(ARQ_ALUNOS) == 0:
        pd.DataFrame(columns=[
            "id_aluno", "nome", "responsavel", "data_matricula",
            "ano_letivo", "valor_mensal", "multa_percentual", "qtd_parcelas", "mes_inicial", "turno"
        ]).to_csv(ARQ_ALUNOS, index=False)
    if not os.path.exists(ARQ_MENSAL) or os.path.getsize(ARQ_MENSAL) == 0:
        pd.DataFrame(columns=[
            "id_mensalidade", "id_aluno", "mes_ano", "valor",
            "vencimento", "data_pagamento", "status", "multa_valor"
        ]).to_csv(ARQ_MENSAL, index=False)

def gerar_proximo_id(df, coluna_id):
    if df.empty or coluna_id not in df.columns:
        return 1
    return int(df[coluna_id].max() + 1)

# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def formatar_valor(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
    except (ValueError, TypeError):
        return "R$ 0,00"

def data_para_texto(data):
    if isinstance(data, date):
        return data.strftime("%d/%m/%Y")
    return str(data).strip() if data else ""

def texto_para_data(texto):
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None

def remover_acentos(texto):
    if not isinstance(texto, str):
        return ""
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII').lower()

def calcular_multa(valor_principal, percentual_multa, dias_atraso=0):
    if dias_atraso <= 0:
        return 0.0
    return round(valor_principal * (percentual_multa / 100), 2)

def carregar_alunos():
    inicializar_arquivos()
    try:
        df = pd.read_csv(ARQ_ALUNOS, dtype={
            "id_aluno": int, "nome": str, "responsavel": str, "data_matricula": str,
            "ano_letivo": int, "valor_mensal": float, "multa_percentual": float,
            "qtd_parcelas": int, "mes_inicial": int, "turno": str
        })
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=[
            "id_aluno", "nome", "responsavel", "data_matricula",
            "ano_letivo", "valor_mensal", "multa_percentual", "qtd_parcelas", "mes_inicial", "turno"
        ])
    if "multa_percentual" not in df.columns:
        df["multa_percentual"] = 0.0
    return df.sort_values(by="nome", ignore_index=True)

def carregar_mensalidades():
    inicializar_arquivos()
    try:
        df = pd.read_csv(ARQ_MENSAL, dtype={
            "id_mensalidade": int, "id_aluno": int, "mes_ano": str, "valor": float,
            "vencimento": str, "data_pagamento": str, "status": str, "multa_valor": float
        })
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=[
            "id_mensalidade", "id_aluno", "mes_ano", "valor",
            "vencimento", "data_pagamento", "status", "multa_valor"
        ])
    if "multa_valor" not in df.columns:
        df["multa_valor"] = 0.0
    return df

def gerar_excel(df, nome_arquivo):
    saida = BytesIO()
    with pd.ExcelWriter(saida, engine='openpyxl') as escritor:
        df.to_excel(escritor, index=False, sheet_name='Relatório')
    saida.seek(0)
    return saida

NOMES_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LISTA_MESES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

# ------------------------------
# INICIALIZAR
# ------------------------------
inicializar_arquivos()
st.set_page_config(page_title="Controle Mensalidades - Versão Web", layout="wide")
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
    df_alunos = carregar_alunos()

    busca = st.text_input("🔍 Buscar por Nome ou Responsável", placeholder="Digite para filtrar...")
    if busca.strip():
        busca_normalizada = remover_acentos(busca)
        df_alunos = df_alunos[
            df_alunos["nome"].apply(remover_acentos).str.contains(busca_normalizada, na=False) |
            df_alunos["responsavel"].apply(remover_acentos).str.contains(busca_normalizada, na=False)
        ]
        df_alunos = df_alunos.sort_values(by="nome", ignore_index=True)

    with st.form("form_aluno", clear_on_submit=True):
        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome Completo")
        resp = col2.text_input("Responsável")
        col3, col4 = st.columns(2)
        
        dt_mat_cal = col3.date_input("📅 Data Matrícula", value=datetime.now(), format="DD/MM/YYYY")
        dt_mat = data_para_texto(dt_mat_cal)
        
        ano = col4.number_input("Ano Letivo", value=datetime.now().year, min_value=2020)
        col5, col6, col7, col8 = st.columns(4)
        valor = col5.text_input("Valor Mensal R$", value="0,00")
        multa_perc = col6.number_input("Multa % fixa por atraso", min_value=0.0, max_value=10.0, step=0.5, value=2.0)
        parcelas = col7.number_input("Nº Parcelas", value=12, min_value=1, max_value=24)
        mes_inic = col8.selectbox("Mês Inicial", NOMES_MESES, index=0)
        turno = st.selectbox("Turno", ["Manhã", "Tarde", "Noite"])
        salvar = st.form_submit_button("💾 Salvar Aluno")

        if salvar:
            erros = []
            if not nome.strip(): erros.append("Informe o nome do aluno")
            if not resp.strip(): erros.append("Informe o responsável")
            try:
                valor_float = float(valor.replace('.', '').replace(',', '.'))
            except:
                erros.append("Valor mensal inválido (use apenas números)")

            if erros:
                for e in erros: st.error(f"❌ {e}")
            else:
                try:
                    mi_num = NOMES_MESES.index(mes_inic) + 1
                    novo_id = gerar_proximo_id(carregar_alunos(), "id_aluno")
                    
                    novo_aluno = pd.DataFrame([{
                        "id_aluno": novo_id, "nome": nome.strip(), "responsavel": resp.strip(),
                        "data_matricula": dt_mat, "ano_letivo": int(ano),
                        "valor_mensal": valor_float, "multa_percentual": float(multa_perc),
                        "qtd_parcelas": int(parcelas), "mes_inicial": mi_num, "turno": turno
                    }])
                    df_alunos_atual = pd.concat([carregar_alunos(), novo_aluno], ignore_index=True)
                    df_alunos_atual.to_csv(ARQ_ALUNOS, index=False)

                    df_mensal = carregar_mensalidades()
                    proximo_id_mensal = gerar_proximo_id(df_mensal, "id_mensalidade")
                    
                    novas_parcelas = []
                    base = mi_num - 1
                    for i in range(int(parcelas)):
                        mes_idx = (base + i) % 12
                        ano_parc = int(ano) + ((base + i) // 12)
                        ma = f"{LISTA_MESES[mes_idx]}/{ano_parc}"
                        ve = f"10/{LISTA_MESES[mes_idx]}/{ano_parc}"
                        
                        novas_parcelas.append({
                            "id_mensalidade": proximo_id_mensal + i,
                            "id_aluno": novo_id, 
                            "mes_ano": ma, 
                            "valor": valor_float,
                            "vencimento": ve, 
                            "data_pagamento": "", 
                            "status": "A Receber",
                            "multa_valor": 0.0
                        })
                    
                    df_mensal = pd.concat([df_mensal, pd.DataFrame(novas_parcelas)], ignore_index=True)
                    df_mensal.to_csv(ARQ_MENSAL, index=False)

                    st.success("✅ Aluno cadastrado! Vencimentos gerados para o dia 10 de cada mês.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar aluno: {str(e)}")

    st.divider()
    st.subheader("Alunos Cadastrados (Ordem Alfabética)")
    if not df_alunos.empty:
        for _, a in df_alunos.iterrows():
            with st.expander(f"{a['nome']} | Responsável: {a['responsavel']}"):
                st.write(f"📅 Matrícula: {a['data_matricula']} | Ano: {a['ano_letivo']}")
                st.write(f"💰 Valor: {formatar_valor(a['valor_mensal'])} | Multa fixa: {a['multa_percentual']}%")
                st.write(f"📆 Parcelas: {a['qtd_parcelas']} | Início: {NOMES_MESES[int(a['mes_inicial'])-1]} | Turno: {a['turno']}")
                
                id_aluno_atual = a["id_aluno"]
                key_editar = f"editar_aluno_{id_aluno_atual}"
                key_conf_excl = f"conf_excl_{id_aluno_atual}"

                if key_editar not in st.session_state:
                    st.session_state[key_editar] = False
                if key_conf_excl not in st.session_state:
                    st.session_state[key_conf_excl] = False

                col_ed, col_ex = st.columns(2)
                if col_ed.button("✏️ Editar", key=f"btn_ed_al_{id_aluno_atual}"):
                    st.session_state[key_editar] = True
                    st.rerun()

                if not st.session_state[key_conf_excl]:
                    if col_ex.button(f"🗑️ Excluir", key=f"btn_excl_{id_aluno_atual}"):
                        st.session_state[key_conf_excl] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Tem certeza que deseja excluir este aluno e todas as suas mensalidades?")
                    col_nao, col_sim = st.columns(2)
                    if col_nao.button("❌ Não", key=f"nao_excl_{id_aluno_atual}"):
                        st.session_state[key_conf_excl] = False
                        st.rerun()
                    if col_sim.button("✅ Sim, excluir", key=f"sim_excl_{id_aluno_atual}"):
                        df_alunos_full = carregar_alunos()
                        df_alunos_full = df_alunos_full[df_alunos_full["id_aluno"] != id_aluno_atual]
                        df_mensal = carregar_mensalidades()
                        df_mensal = df_mensal[df_mensal["id_aluno"] != id_aluno_atual]
                        df_alunos_full.to_csv(ARQ_ALUNOS, index=False)
                        df_mensal.to_csv(ARQ_MENSAL, index=False)
                        st.success("✅ Aluno e mensalidades excluídos com sucesso!")
                        st.session_state[key_conf_excl] = False
                        st.rerun()

                if st.session_state[key_editar]:
                    st.divider()
                    st.subheader("Editar Dados do Aluno")
                    
                    dt_mat_atual = texto_para_data(a["data_matricula"]) or datetime.now().date()
                    
                    with st.form(f"form_editar_aluno_{id_aluno_atual}", clear_on_submit=False):
                        e_nome = st.text_input("Nome Completo", value=a["nome"])
                        e_resp = st.text_input("Responsável", value=a["responsavel"])
                        
                        e_dt_mat_cal = st.date_input("📅 Data Matrícula", value=dt_mat_atual, format="DD/MM/YYYY")
                        e_dt_mat = data_para_texto(e_dt_mat_cal)
                        
                        e_ano = st.number_input("Ano Letivo", value=int(a["ano_letivo"]), min_value=2020)
                        e_valor = st.text_input("Valor Mensal R$", value=str(a["valor_mensal"]).replace('.', ','))
                        e_multa = st.number_input("Multa % fixa por atraso", min_value=0.0, max_value=10.0, step=0.5, value=float(a["multa_percentual"]))
                        e_parc = st.number_input("Nº Parcelas", value=int(a["qtd_parcelas"]), min_value=1, max_value=24)
                        e_mes_inic = st.selectbox("Mês Inicial", NOMES_MESES, index=int(a["mes_inicial"])-1)
                        e_turno = st.selectbox("Turno", ["Manhã", "Tarde", "Noite"], index=["Manhã", "Tarde", "Noite"].index(a["turno"]))

                        salva_ed = st.form_submit_button("💾 Salvar Alterações")
                        cancela_ed = st.form_submit_button("❌ Cancelar")

                        if cancela_ed:
                            st.session_state[key_editar] = False
                            st.rerun()

                        if salva_ed:
                            erros_ed = []
                            if not e_nome.strip(): erros_ed.append("Informe o nome do aluno")
                            if not e_resp.strip(): erros_ed.append("Informe o responsável")
                            try:
                                float(e_valor.replace('.', '').replace(',', '.'))
                            except:
                                erros_ed.append("Valor mensal inválido")

                            if erros_ed:
                                for err in erros_ed: st.error(f"❌ {err}")
                            else:
                                try:
                                    df_alunos_full = carregar_alunos()
                                    df_alunos_full.loc[df_alunos_full["id_aluno"] == id_aluno_atual, [
                                        "nome", "responsavel", "data_matricula", "ano_letivo",
                                        "valor_mensal", "multa_percentual", "qtd_parcelas", "mes_inicial", "turno"
                                    ]] = [
                                        e_nome.strip(), e_resp.strip(), e_dt_mat, int(e_ano),
                                        float(e_valor.replace('.', '').replace(',', '.')), float(e_multa),
                                        int(e_parc), NOMES_MESES.index(e_mes_inic) + 1, e_turno
                                    ]
                                    df_alunos_full.to_csv(ARQ_ALUNOS, index=False)
                                    st.success("✅ Dados do aluno atualizados!")
                                    st.session_state[key_editar] = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao editar: {str(e)}")
    else:
        if busca.strip():
            st.info("ℹ️ Nenhum aluno encontrado com esse termo. Apague o texto para ver todos.")
        else:
            st.info("ℹ️ Nenhum aluno cadastrado ainda.")

# ------------------------------
# TELA DE MENSALIDADES
# ------------------------------
elif menu == "Mensalidades":
    st.subheader("Controle de Mensalidades")
    df_alunos = carregar_alunos()
    df_mensal = carregar_mensalidades()
    hoje_dt = date.today()

    if df_alunos.empty:
        st.warning("⚠️ Cadastre um aluno primeiro!")
    else:
        st.info("💡 Clique no nome do aluno para ver e gerenciar suas parcelas")
        st.divider()

        for _, aluno in df_alunos.iterrows():
            id_aluno = aluno["id_aluno"]
            multa_perc_aluno = float(aluno["multa_percentual"])
            mensais = df_mensal[df_mensal["id_aluno"] == id_aluno].copy()

            qtde_atrasadas = len(mensais[(mensais["status"] == "A Receber") & (pd.to_datetime(mensais["vencimento"], format="%d/%m/%Y", errors="coerce").dt.date < hoje_dt)])
            qtde_receber = len(mensais[(mensais["status"] == "A Receber") & (pd.to_datetime(mensais["vencimento"], format="%d/%m/%Y", errors="coerce").dt.date >= hoje_dt)])
            qtde_pagas = len(mensais[mensais["status"] == "Quitada"])

            titulo_exp = f"📌 {aluno['nome']} | Atrasadas: {qtde_atrasadas} | A Receber: {qtde_receber} | Pagas: {qtde_pagas}"

            with st.expander(titulo_exp):
                if mensais.empty:
                    st.info("Nenhuma parcela gerada para este aluno.")
                    continue

                st.divider()
                for idx, m in mensais.iterrows():
                    status_exib = m["status"]
                    dias_atraso = 0
                    multa_calculada = 0.0

                    venc_dt = texto_para_data(str(m["vencimento"]))
                    if venc_dt and status_exib == "A Receber" and venc_dt < hoje_dt:
                        dias_atraso = (hoje_dt - venc_dt).days
                        status_exib = "Atrasada"
                        multa_calculada = calcular_multa(float(m["valor"]), multa_perc_aluno, dias_atraso)
                        if float(m["multa_valor"]) != multa_calculada:
                            df_mensal.at[idx, "multa_valor"] = multa_calculada
                            df_mensal.to_csv(ARQ_MENSAL, index=False)

                    cor = "🔴" if status_exib == "Atrasada" else ("🟢" if status_exib == "Quitada" else "🟡")
                    dt_pag_exib = m["data_pagamento"] if str(m["data_pagamento"]).strip() else "--"
                    multa_exib = formatar_valor(m["multa_valor"]) if float(m["multa_valor"]) > 0 else "R$ 0,00"
                    total_exib = formatar_valor(float(m["valor"]) + float(m["multa_valor"]))
                    
                    with st.container(border=True):
                        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1.2, 1.3, 1.3, 1.3, 1.3, 1.5, 1.5, 1])
                        col1.write(f"**{m['mes_ano']}**")
                        col2.write(formatar_valor(m["valor"]))
                        col3.write(f"Venc: {m['vencimento']}")
                        col4.write(f"Pagto: {dt_pag_exib}")
                        col5.write(f"Multa: {multa_exib}")
                        col6.write(f"Total: {total_exib}")
                        col7.write(f"{cor} {status_exib}")
                        
                        if col8.button("Editar", key=f"btn_editar_{idx}"):
                            st.session_state["editando_idx"] = idx

                        if st.session_state.get("editando_idx") == idx:
                            with st.form(f"form_parcela_{idx}", clear_on_submit=False):
                                novo_valor = st.text_input("Valor R$", value=str(m["valor"]).replace('.', ','))
                                
                                venc_atual = texto_para_data(str(m["vencimento"])) or hoje_dt
                                dt_pg_atual = texto_para_data(str(m["data_pagamento"])) or None
                                
                                novo_venc_cal = st.date_input("📅 Vencimento", value=venc_atual, format="DD/MM/YYYY")
                                novo_venc = data_para_texto(novo_venc_cal)
                                
                                nova_multa = st.text_input("Multa R$", value=str(m["multa_valor"]).replace('.', ','))
                                novo_status = st.selectbox("Status", ["A Receber", "Quitada"], index=0 if m["status"] == "A Receber" else 1)
                                
                                dt_pg_cal = st.date_input("📅 Data Pagamento (se quitada)", value=dt_pg_atual, format="DD/MM/YYYY")
                                dt_pg = data_para_texto(dt_pg_cal) if novo_status == "Quitada" else ""
                                
                                if st.form_submit_button("Salvar Alteração"):
                                    erros = []
                                    try:
                                        float(novo_valor.replace('.', '').replace(',', '.'))
                                    except:
                                        erros.append("Valor inválido")
                                    try:
                                        float(nova_multa.replace('.', '').replace(',', '.'))
                                    except:
                                        erros.append("Valor da multa inválido")

                                    if erros:
                                        for e in erros: st.error(f"❌ {e}")
                                    else:
                                        try:
                                            df_mensal.at[idx, "valor"] = float(novo_valor.replace('.', '').replace(',', '.'))
                                            df_mensal.at[idx, "vencimento"] = novo_venc
                                            df_mensal.at[idx, "multa_valor"] = float(nova_multa.replace('.', '').replace(',', '.'))
                                            df_mensal.at[idx, "status"] = novo_status
                                            df_mensal.at[idx, "data_pagamento"] = dt_pg
                                            
                                            df_mensal.to_csv(ARQ_MENSAL, index=False)
                                            st.success("✅ Parcela atualizada!")
                                            del st.session_state["editando_idx"]
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro: {str(e)}")

# ------------------------------
# RELATÓRIOS
# ------------------------------
elif menu == "Relatórios":
    st.subheader("Relatórios Financeiros")
    tipo = st.radio("Escolha o tipo de relatório:", ["Todos", "A Receber", "Atrasadas", "Quitadas", "Por Período"], horizontal=True)
    
    df_alunos = carregar_alunos()
    df_mensal = carregar_mensalidades()
    hoje_dt = date.today()
    hoje_str = datetime.now().strftime("%d/%m/%Y")
    
    dados = None
    titulo_rel = ""

    if not df_mensal.empty and not df_alunos.empty:
        df_completo = df_mensal.merge(df_alunos, on="id_aluno", how="left")
        df_completo["vencimento_dt"] = pd.to_datetime(df_completo["vencimento"], format="%d/%m/%Y", errors="coerce").dt.date
        df_completo["total_com_multa"] = df_completo["valor"] + df_completo["multa_valor"]

        if tipo == "Por Período":
            st.write("---")
            col_d1, col_d2 = st.columns(2)
            
            dt_inicio_cal = col_d1.date_input("📅 Data Início", value=date(2026,1,1), format="DD/MM/YYYY")
            dt_fim_cal = col_d2.date_input("📅 Data Fim", value=hoje_dt, format="DD/MM/YYYY")
            dt_inicio_str = data_para_texto(dt_inicio_cal)
            dt_fim_str = data_para_texto(dt_fim_cal)
            
            status_periodo = st.radio("Filtrar por Status", ["Todos", "A Receber", "Atrasadas", "Quitadas"], horizontal=True)
            
            titulo_rel = f"Relatório: {status_periodo} | Período: {dt_inicio_str} até {dt_fim_str}"

            d_inicio = dt_inicio_cal
            d_fim = dt_fim_cal

            dados = df_completo[(df_completo["vencimento_dt"] >= d_inicio) & (df_completo["vencimento_dt"] <= d_fim)]

            if status_periodo == "A Receber":
                dados = dados[(dados["status"] == "A Receber") & (dados["vencimento_dt"] >= hoje_dt)]
            elif status_periodo == "Atrasadas":
                dados = dados[(dados["status"] == "A Receber") & (dados["vencimento_dt"] < hoje_dt)]
            elif status_periodo == "Quitadas":
                dados = dados[dados["status"] == "Quitada"]

        elif tipo == "Todos":
            titulo_rel = "Relatório Geral de Mensalidades"
            dados = df_completo
        elif tipo == "A Receber":
            titulo_rel = "Relatório - Mensalidades A Receber"
            dados = df_completo[(df_completo["status"] == "A Receber") & (df_completo["vencimento_dt"] >= hoje_dt)]
        elif tipo == "Atrasadas":
            titulo_rel = "Relatório - Mensalidades Atrasadas"
            dados = df_completo[(df_completo["status"] == "A Receber") & (df_completo["vencimento_dt"] < hoje_dt)]
        elif tipo == "Quitadas":
            titulo_rel = "Relatório - Mensalidades Quitadas"
            dados = df_completo[df_completo["status"] == "Quitada"]

    if dados is not None and not dados.empty:
        exibe = dados[["nome", "mes_ano", "valor", "multa_valor", "total_com_multa", "vencimento", "data_pagamento", "status"]].copy()
        exibe["data_pagamento"] = exibe["data_pagamento"].replace("", "--")
        exibe["valor"] = exibe["valor"].apply(formatar_valor)
        exibe["multa_valor"] = exibe["multa_valor"].apply(formatar_valor)
        exibe["total_com_multa"] = exibe["total_com_multa"].apply(formatar_valor)
        total_geral = dados["valor"].sum() + dados["multa_valor"].sum()

        st.subheader(titulo_rel)
        st.dataframe(exibe, use_container_width=True)
        st.subheader(f"Total Geral (com multas): {formatar_valor(total_geral)}")

        st.divider()
        col_imp, col_exp = st.columns(2)
        with col_imp:
            if st.button("🖨️ Gerar Visualização para Impressão"):
                st.markdown(f"<h2 style='text-align:center;'>{titulo_rel}</h2><p style='text-align:center;'>Emitido em: {hoje_str}</p><hr>", unsafe_allow_html=True)
                st.table(exibe)
                st.markdown(f"<div style='text-align:right; font-weight:bold; font-size:18px;'>Total Geral: {formatar_valor(total_geral)}</div>", unsafe_allow_html=True)
                st.info("💡 Use Ctrl+P no navegador para salvar em PDF ou imprimir.")
        with col_exp:
            excel = gerar_excel(exibe, titulo_rel.replace(" ", "_"))
            st.download_button(
                label="📥 Baixar Relatório em Excel",
                data=excel,
                file_name=f"{titulo_rel.replace(' ', '_')}_{hoje_str.replace('/', '-')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("ℹ️ Nenhum registro encontrado para os filtros selecionados.")
