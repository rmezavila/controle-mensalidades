import streamlit as st
import json
from datetime import datetime
import os
import urllib.parse

ARQUIVO_CONFIG = "config_sistema.json"
ARQUIVO_CLIENTES = "clientes_streamlit.json"
ARQUIVO_AGENDAMENTOS = "agendamentos_streamlit.json"

# ========== CARREGAR CONFIGURAÇÃO ==========
def carregar_config():
    if not os.path.exists(ARQUIVO_CONFIG):
        return {"senha_admin": ""}
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"senha_admin": ""}

def salvar_config(config):
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def carregar_dados(arquivo):
    if not os.path.exists(arquivo):
        return []
    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def salvar_dados(dados, arquivo):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# ========== CONFIGURAÇÃO DA PÁGINA ==========
st.set_page_config(
    page_title="Salão Abelhinha",
    page_icon="🐝",
    layout="centered",
    menu_items={}
)

# Esconder apenas o rodapé e marcações — SEM EXTRAS
st.markdown("""
<style>
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

hoje = datetime.today().date()
config = carregar_config()

# ========== TELA DE PRIMEIRO ACESSO ==========
if not config.get("senha_admin"):
    st.title("🐝 Bem-vindo!")
    st.info("É seu primeiro acesso. Crie uma senha para entrar.")
    senha1 = st.text_input("Digite sua senha", type="password")
    senha2 = st.text_input("Repita a senha", type="password")
    if st.button("✅ Criar Senha"):
        if len(senha1) < 3:
            st.error("Use pelo menos 3 caracteres.")
        elif senha1 != senha2:
            st.error("As senhas são diferentes.")
        else:
            config["senha_admin"] = senha1
            salvar_config(config)
            st.success("Senha criada! Faça login.")
    st.stop()

# ========== TELA DE LOGIN ==========
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acesso Restrito")
    senha = st.text_input("Digite sua senha", type="password")
    if st.button("Entrar"):
        if senha == config["senha_admin"]:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    st.stop()

# ========== USUÁRIO LOGADO ==========
st.sidebar.title("💄 Salão Abelhinha")
pagina = st.sidebar.selectbox("Menu", 
    ["📅 Agendar", "👥 Clientes", "📖 Agendamentos", "⚙️ Senha"])
if st.sidebar.button("Sair"):
    st.session_state.autenticado = False
    st.rerun()

SERVICOS = {"Manicure":25, "Pedicure":30, "Manicure+Pedicure":50, 
            "Hidratação":60, "Corte":70, "Coloração":90, "Escova":35}

# ========== ALTERAR SENHA ==========
if pagina == "⚙️ Senha":
    st.title("Alterar Senha")
    atual = st.text_input("Senha Atual", type="password")
    n1 = st.text_input("Nova Senha", type="password")
    n2 = st.text_input("Repita Nova Senha", type="password")
    if st.button("Salvar"):
        if atual == config["senha_admin"] and n1 == n2 and len(n1)>=3:
            config["senha_admin"] = n1
            salvar_config(config)
            st.success("Senha alterada!")
        else:
            st.error("Verifique os dados.")

# ========== AGENDAR ==========
elif pagina == "📅 Agendar":
    st.title("📅 Novo Agendamento")
    clientes = carregar_dados(ARQUIVO_CLIENTES)
    lista = [c["nome"]+" — "+c["telefone"] for c in clientes]
    escolha = st.selectbox("Cliente", [""]+lista)
    serv = st.selectbox("Serviço", list(SERVICOS.keys()))
    valor = SERVICOS[serv]
    data = st.date_input("Data", value=hoje, format="DD/MM/YYYY")
    hora = st.time_input("Hora")
    if st.button("✅ Agendar"):
        if escolha:
            nome = escolha.split(" — ")[0]
            tel = escolha.split(" — ")[1]
            ag = carregar_dados(ARQUIVO_AGENDAMENTOS)
            ag.append({"cliente":nome, "servico":serv, "valor":valor, 
                      "data":data.strftime("%d/%m/%Y"), "hora":hora.strftime("%H:%M")})
            salvar_dados(ag, ARQUIVO_AGENDAMENTOS)
            st.success(f"Agendado para {nome}!")
            tel_num = ''.join(filter(str.isdigit, tel))
            msg = f"Olá {nome}! Agendamento: {serv} dia {data.strftime('%d/%m/%Y')} às {hora.strftime('%H:%M')}. Valor R${valor}"
            st.markdown(f"[📱 Enviar WhatsApp](https://wa.me/55{tel_num}?text={urllib.parse.quote(msg)})")
        else:
            st.warning("Escolha um cliente.")

# ========== CLIENTES ==========
elif pagina == "👥 Clientes":
    st.title("👥 Clientes")
    nome = st.text_input("Nome Completo")
    tel = st.text_input("WhatsApp")
    if st.button("Cadastrar"):
        if nome and tel:
            cl = carregar_dados(ARQUIVO_CLIENTES)
            cl.append({"nome":nome, "telefone":tel})
            salvar_dados(cl, ARQUIVO_CLIENTES)
            st.success("Cadastrado!")
            st.rerun()
        else:
            st.warning("Preencha tudo.")
    st.divider()
    cl = carregar_dados(ARQUIVO_CLIENTES)
    st.table(cl)

# ========== LISTA AGENDAMENTOS ==========
elif pagina == "📖 Agendamentos":
    st.title("📖 Agendamentos")
    ag = carregar_dados(ARQUIVO_AGENDAMENTOS)
    st.table(ag)
