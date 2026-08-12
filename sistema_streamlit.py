# import tkinter as tk
# from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import shutil
import os
import subprocess
import sys

# ------------------------------
# BANCO DE DADOS
# ------------------------------
def conectar():
    return sqlite3.connect('controle_mensalidades_novo.db', timeout=5)

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
# BACKUP AUTOMÁTICO
# ------------------------------
def fazer_backup():
    try:
        arq = "controle_mensalidades_novo.db"
        pasta = "BACKUPS"
        if not os.path.exists(pasta):
            os.makedirs(pasta)
        dh = datetime.now().strftime("%Y%m%d_%H%M")
        shutil.copy2(arq, os.path.join(pasta, f"backup_{dh}.db"))
        arquivos = sorted(
            [os.path.join(pasta, f) for f in os.listdir(pasta) if f.startswith("backup_")],
            key=os.path.getmtime
        )
        if len(arquivos) > 10:
            os.remove(arquivos[0])
    except Exception as e:
        print(f"Erro no backup: {e}")

# ------------------------------
# FUNÇÕES AUXILIARES
# ------------------------------
def formatar_valor(valor):
    return f"R$ {valor:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

def data_valida(data):
    try:
        datetime.strptime(data.strip(), "%d/%m/%Y")
        return True
    except (ValueError, TypeError, AttributeError):
        return False

NOMES_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
               "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LISTA_MESES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]

# ------------------------------
# JANELA DE RELATÓRIO
# ------------------------------
class Relatorio(tk.Toplevel):
    def __init__(self, mestre, titulo, texto, periodo=""):
        super().__init__(mestre)
        self.title(titulo)
        self.geometry("850x600")
        self.transient(mestre)
        self.grab_set()

        quadro = ttk.Frame(self, padding=10)
        quadro.pack(fill=tk.BOTH, expand=True)

        ttk.Label(quadro, text=titulo, font=("Arial", 14, "bold")).pack(pady=5)
        if periodo:
            ttk.Label(quadro, text=f"Período: {periodo}", font=("Arial", 11, "italic")).pack(pady=2)

        self.texto = tk.Text(quadro, font=("Courier New", 9), wrap=tk.NONE)
        v = ttk.Scrollbar(quadro, orient="vertical", command=self.texto.yview)
        h = ttk.Scrollbar(quadro, orient="horizontal", command=self.texto.xview)
        self.texto.configure(yscrollcommand=v.set, xscrollcommand=h.set)
        v.pack(side=tk.RIGHT, fill=tk.Y)
        h.pack(side=tk.BOTTOM, fill=tk.X)
        self.texto.pack(fill=tk.BOTH, expand=True)
        self.texto.insert("1.0", texto)
        self.texto.config(state="disabled")

        botoes = ttk.Frame(self, padding=5)
        botoes.pack(fill=tk.X)
        ttk.Button(botoes, text="🖨️ Imprimir", command=self.imprimir).pack(side=tk.LEFT, padx=5)
        ttk.Button(botoes, text="❌ Fechar", command=self.destroy).pack(side=tk.RIGHT, padx=5)

        self.conteudo = f"{titulo}\n"
        if periodo:
            self.conteudo += f"Período: {periodo}\n"
        self.conteudo += f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n" + "-" * 65 + "\n\n" + texto

    def imprimir(self):
        try:
            temp = os.path.join(os.environ.get("TEMP", "."), "rel_temp.txt")
            with open(temp, "w", encoding="utf-8") as f:
                f.write("\f" + self.conteudo + "\n\n")

            if sys.platform == "win32":
                subprocess.run(["notepad.exe", "/p", temp], check=True)
                messagebox.showinfo("Sucesso", "Relatório enviado para a impressora!")
            else:
                messagebox.showinfo("Aviso", f"Arquivo salvo em:\n{temp}\nImprima manualmente.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível imprimir:\n{e}\nArquivo: {temp}")

# ------------------------------
# TELA PRINCIPAL
# ------------------------------
class Sistema:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("Controle de Mensalidades - SALVAR ALUNO CORRIGIDO")
        self.janela.geometry("1280x720")
        criar_banco()
        fazer_backup()

        self.id_aluno = None
        self.id_mensal = None
        self.lista_alunos = []

        self.cor_atrasada = "#ffd6d6"
        self.cor_quitada = "#d6ffd6"
        self.cor_receber = "#ffffd6"

        self.montar_interface()
        self.carregar_alunos()

    def montar_interface(self):
        # Menu
        menu = tk.Menu(self.janela)
        self.janela.config(menu=menu)
        menu_rel = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Relatórios", menu=menu_rel)
        menu_rel.add_command(label="Todos os Alunos", command=lambda: self.rel_todos())
        menu_rel.add_separator()
        menu_rel.add_command(label="A Receber", command=lambda: self.rel_a_receber())
        menu_rel.add_command(label="Atrasadas", command=lambda: self.rel_atrasadas())
        menu_rel.add_command(label="Quitadas", command=lambda: self.rel_quitadas())
        menu_rel.add_separator()
        menu_rel.add_command(label="Por Período", command=self.rel_periodo)

        ttk.Label(self.janela, text="Controle de Mensalidades", font=("Arial", 16, "bold")).pack(pady=10)

        principal = ttk.Frame(self.janela, padding=10)
        principal.pack(fill=tk.BOTH, expand=True)

        # Lado esquerdo
        esq = ttk.LabelFrame(principal, text="Alunos Cadastrados", padding=8)
        esq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.lista_box = tk.Listbox(esq, width=30, height=25, font=("Arial", 10))
        self.lista_box.pack(fill=tk.BOTH, expand=True)
        self.lista_box.bind("<<ListboxSelect>>", self.selecionar_aluno)

        ttk.Button(esq, text="Atualizar Lista", command=self.carregar_alunos).pack(fill=tk.X, pady=3)
        ttk.Button(esq, text="Ver e Imprimir Aluno", command=self.imprimir_aluno).pack(fill=tk.X, pady=3)
        ttk.Button(esq, text="🗑️ Excluir Aluno", command=self.excluir_aluno).pack(fill=tk.X, pady=3)

        # Lado direito
        dir_frame = ttk.Frame(principal)
        dir_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Button(dir_frame, text="+ Novo Aluno", command=self.limpar_campos).pack(anchor="w", pady=(0, 8))

        quadro_aluno = ttk.LabelFrame(dir_frame, text="Dados do Aluno", padding=10)
        quadro_aluno.pack(fill=tk.X, pady=5)

        ttk.Label(quadro_aluno, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.nome = ttk.Entry(quadro_aluno, width=35)
        self.nome.grid(row=0, column=1, padx=5)

        ttk.Label(quadro_aluno, text="Responsável:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.resp = ttk.Entry(quadro_aluno, width=30)
        self.resp.grid(row=0, column=3, padx=5)

        ttk.Label(quadro_aluno, text="Data Matrícula:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.dt_mat = ttk.Entry(quadro_aluno, width=12)
        self.dt_mat.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.dt_mat.grid(row=1, column=1, padx=5)

        ttk.Label(quadro_aluno, text="Ano Letivo:").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.ano = ttk.Entry(quadro_aluno, width=8)
        self.ano.insert(0, str(datetime.now().year))
        self.ano.grid(row=1, column=3, padx=5)

        ttk.Label(quadro_aluno, text="Valor Mensal R$:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.valor = ttk.Entry(quadro_aluno, width=12)
        self.valor.grid(row=2, column=1, padx=5)

        ttk.Label(quadro_aluno, text="Parcelas:").grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.parcelas = ttk.Entry(quadro_aluno, width=6)
        self.parcelas.insert(0, "12")
        self.parcelas.grid(row=2, column=3, padx=5)

        ttk.Label(quadro_aluno, text="Mês Inicial:").grid(row=2, column=4, padx=5, pady=5, sticky="w")
        self.mes_inic = ttk.Combobox(quadro_aluno, values=NOMES_MESES, state="readonly", width=12)
        self.mes_inic.current(0)
        self.mes_inic.grid(row=2, column=5, padx=5)

        ttk.Label(quadro_aluno, text="Turno:").grid(row=2, column=6, padx=5, pady=5, sticky="w")
        self.turno = ttk.Combobox(quadro_aluno, values=["Manhã", "Tarde", "Noite"], state="readonly", width=10)
        self.turno.current(0)
        self.turno.grid(row=2, column=7, padx=5)

        ttk.Button(quadro_aluno, text="💾 Salvar Aluno", command=self.salvar_aluno).grid(row=3, column=0, columnspan=8, pady=10)

        # Controle de Mensalidades
        quadro_mensal = ttk.LabelFrame(dir_frame, text="Controle de Mensalidades", padding=10)
        quadro_mensal.pack(fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(quadro_mensal, text="Mês/Ano:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.mesano = ttk.Entry(quadro_mensal, width=10, state="readonly")
        self.mesano.grid(row=0, column=1, padx=5)

        ttk.Label(quadro_mensal, text="Valor R$:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.valor_mes = ttk.Entry(quadro_mensal, width=12)
        self.valor_mes.grid(row=0, column=3, padx=5)

        ttk.Label(quadro_mensal, text="Vencimento:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.venc = ttk.Entry(quadro_mensal, width=12)
        self.venc.grid(row=0, column=5, padx=5)

        ttk.Label(quadro_mensal, text="Status:").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.status = ttk.Combobox(quadro_mensal, values=["A Receber", "Quitada"], state="readonly", width=12)
        self.status.current(0)
        self.status.bind("<<ComboboxSelected>>", self.mostrar_data_pagamento)
        self.status.grid(row=0, column=7, padx=5)

        self.lbl_pag = ttk.Label(quadro_mensal, text="Data Pagamento:")
        self.data_pag = ttk.Entry(quadro_mensal, width=12)
        self.data_pag.insert(0, datetime.now().strftime("%d/%m/%Y"))

        # Tabela
        self.tabela = ttk.Treeview(quadro_mensal, columns=("mes", "valor", "venc", "pag", "status"), show="headings", height=10)
        self.tabela.heading("mes", text="Mês/Ano")
        self.tabela.heading("valor", text="Valor")
        self.tabela.heading("venc", text="Vencimento")
        self.tabela.heading("pag", text="Pagamento")
        self.tabela.heading("status", text="Status")

        self.tabela.column("mes", width=90, anchor="center")
        self.tabela.column("valor", width=110, anchor="center")
        self.tabela.column("venc", width=110, anchor="center")
        self.tabela.column("pag", width=110, anchor="center")
        self.tabela.column("status", width=100, anchor="center")

        self.tabela.tag_configure("atrasada", background=self.cor_atrasada)
        self.tabela.tag_configure("quitada", background=self.cor_quitada)
        self.tabela.tag_configure("receber", background=self.cor_receber)

        self.tabela.bind("<<TreeviewSelect>>", self.selecionar_mensal)
        barra = ttk.Scrollbar(quadro_mensal, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        barra.grid(row=1, column=9, sticky="ns")
        self.tabela.grid(row=1, column=0, columnspan=9, sticky="nsew", pady=10)

        quadro_mensal.grid_rowconfigure(1, weight=1)
        quadro_mensal.grid_columnconfigure(0, weight=1)

        rodape = ttk.Frame(quadro_mensal)
        rodape.grid(row=2, column=0, columnspan=9, sticky="ew")
        ttk.Button(rodape, text="Quitar / Atualizar", command=self.atualizar_mensalidade).pack(side=tk.LEFT, padx=5)
        ttk.Button(rodape, text="Ver e Imprimir Recibo", command=self.imprimir_recibo).pack(side=tk.RIGHT, padx=5)

    def mostrar_data_pagamento(self, evento=None):
        if self.status.get() == "Quitada":
            self.lbl_pag.grid(row=0, column=8, padx=5, pady=5, sticky="w")
            self.data_pag.grid(row=0, column=9, padx=5)
        else:
            self.lbl_pag.grid_remove()
            self.data_pag.grid_remove()

    def excluir_aluno(self):
        if not self.id_aluno:
            messagebox.showwarning("Aviso", "Selecione um aluno na lista primeiro!")
            return
        sel = self.lista_box.get(self.lista_box.curselection())
        confirma = messagebox.askyesno("Confirmação", f"Excluir aluno:\n{sel}?\nEssa ação não pode ser desfeita!")
        if not confirma:
            return
        conn = conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM alunos WHERE id_aluno=?", (self.id_aluno,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Aluno excluído!")
        self.limpar_campos()
        self.carregar_alunos()

    def carregar_alunos(self):
        self.lista_box.delete(0, tk.END)
        self.lista_alunos = []
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id_aluno, nome FROM alunos ORDER BY nome")
        self.lista_alunos = cur.fetchall()
        for _, n in self.lista_alunos:
            self.lista_box.insert(tk.END, n)
        conn.close()

    def selecionar_aluno(self, evt):
        sel = self.lista_box.curselection()
        if not sel:
            return
        self.id_aluno = self.lista_alunos[sel[0]][0]
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT * FROM alunos WHERE id_aluno=?", (self.id_aluno,))
        d = cur.fetchone()
        conn.close()
        self.nome.delete(0, tk.END); self.nome.insert(0, d[1])
        self.resp.delete(0, tk.END); self.resp.insert(0, d[2])
        self.dt_mat.delete(0, tk.END); self.dt_mat.insert(0, d[3])
        self.ano.delete(0, tk.END); self.ano.insert(0, str(d[4]))
        self.valor.delete(0, tk.END); self.valor.insert(0, f"{d[5]:.2f}".replace('.', ','))
        self.parcelas.delete(0, tk.END); self.parcelas.insert(0, str(d[6]))
        self.mes_inic.current(d[7] - 1)
        self.turno.set(d[8])
        self.carregar_mensalidades()

    def carregar_mensalidades(self):
        for i in self.tabela.get_children():
            self.tabela.delete(i)
        if not self.id_aluno:
            return
        conn = conectar()
        cur = conn.cursor()
        hoje = datetime.now().strftime("%d/%m/%Y")
        cur.execute("SELECT id_mensalidade, mes_ano, valor, vencimento, data_pagamento, status FROM mensalidades WHERE id_aluno=? ORDER BY mes_ano", (self.id_aluno,))
        for im, ma, v, ve, p, s in cur.fetchall():
            sexib = "Atrasada" if s == "A Receber" and data_valida(ve) and datetime.strptime(ve, "%d/%m/%Y") < datetime.strptime(hoje, "%d/%m/%Y") else s
            tag = "atrasada" if sexib == "Atrasada" else ("quitada" if s == "Quitada" else "receber")
            self.tabela.insert("", "end", iid=str(im), values=(ma, formatar_valor(v), ve, p or "-", sexib), tags=(tag,))
        conn.close()

    def selecionar_mensal(self, evt):
        sel = self.tabela.selection()
        if not sel:
            return
        self.id_mensal = int(sel[0])
        d = self.tabela.item(sel[0], "values")
        self.mesano.config(state="normal")
        self.mesano.delete(0, tk.END); self.mesano.insert(0, d[0])
        self.mesano.config(state="readonly")
        self.valor_mes.delete(0, tk.END); self.valor_mes.insert(0, d[1].replace("R$ ", "").replace(",", "."))
        self.venc.delete(0, tk.END); self.venc.insert(0, d[2])
        status_exibido = d[4]
        self.status.set("A Receber" if status_exibido == "Atrasada" else status_exibido)
        if d[3] != "-":
            self.data_pag.delete(0, tk.END); self.data_pag.insert(0, d[3])
        else:
            self.data_pag.delete(0, tk.END); self.data_pag.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.mostrar_data_pagamento()

    # =====================================================
    # 🔑 FUNÇÃO SALVAR ALUNO — CORRIGIDA E SIMPLIFICADA
    # =====================================================
    def salvar_aluno(self):
        # Pegar e limpar todos os campos
        n = self.nome.get().strip()
        r = self.resp.get().strip()
        dt = self.dt_mat.get().strip()
        a = self.ano.get().strip()
        v = self.valor.get().strip()
        p = self.parcelas.get().strip()
        mi = self.mes_inic.current() + 1
        t = self.turno.get()

        # ✅ Validações claras com mensagens específicas
        if not n:
            messagebox.showwarning("Aviso", "Digite o NOME do aluno!")
            self.nome.focus()
            return
        if not r:
            messagebox.showwarning("Aviso", "Digite o RESPONSÁVEL!")
            self.resp.focus()
            return
        if not data_valida(dt):
            messagebox.showwarning("Aviso", f"Data de matrícula inválida: {dt}\nUse o formato DD/MM/AAAA")
            self.dt_mat.focus()
            return
        if not a.isdigit():
            messagebox.showwarning("Aviso", f"Ano inválido: {a}\nDigite apenas números, ex: 2026")
            self.ano.delete(0, tk.END); self.ano.insert(0, str(datetime.now().year))
            self.ano.focus()
            return
        if not v:
            messagebox.showwarning("Aviso", "Digite o VALOR MENSAL!")
            self.valor.focus()
            return
        if not p.isdigit() or int(p) <= 0:
            messagebox.showwarning("Aviso", "Quantidade de PARCELAS inválida!\nDigite um número maior que zero.")
            self.parcelas.delete(0, tk.END); self.parcelas.insert(0, "12")
            self.parcelas.focus()
            return

        # ✅ Conversão segura
        try:
            ano_int = int(a)
            valor_str = v.replace('R$', '').replace(' ', '').replace(',', '.')
            valor_float = float(valor_str)
            parcelas_int = int(p)
            if valor_float <= 0:
                messagebox.showwarning("Aviso", "Valor mensal deve ser maior que zero!")
                self.valor.focus()
                return
        except Exception as e:
            messagebox.showwarning("Aviso", f"Erro nos valores:\n{e}\nVerifique valor e parcelas.")
            return

        # ✅ SALVAR no banco
        try:
            conn = conectar()
            cur = conn.cursor()

            if not self.id_aluno:
                # NOVO ALUNO
                cur.execute(
                    "INSERT INTO alunos VALUES (NULL,?,?,?,?,?,?,?,?)",
                    (n, r, dt, ano_int, valor_float, parcelas_int, mi, t)
                )
                self.id_aluno = cur.lastrowid
                mensagem = "✅ Aluno cadastrado com sucesso!"
            else:
                # EDITAR ALUNO EXISTENTE
                cur.execute(
                    "UPDATE alunos SET nome=?, responsavel=?, data_matricula=?, ano_letivo=?, valor_mensal=?, qtd_parcelas=?, mes_inicial=?, turno=? WHERE id_aluno=?",
                    (n, r, dt, ano_int, valor_float, parcelas_int, mi, t, self.id_aluno)
                )
                mensagem = "✅ Aluno atualizado com sucesso!"

            conn.commit()
            conn.close()

            # ✅ Gerar mensalidades APÓS confirmar salvamento
            self.gerar_mensalidades(ano_int, valor_float, parcelas_int, mi)

            # ✅ Atualizar interface
            self.carregar_alunos()
            self.carregar_mensalidades()
            messagebox.showinfo("Sucesso", mensagem)

        except Exception as e:
            messagebox.showerror("ERRO ao salvar", f"Não foi possível salvar:\n{str(e)}")

    # =====================================================
    # 🔑 GERAÇÃO DE MENSALIDADES — CORRIGIDA
    # =====================================================
    def gerar_mensalidades(self, ano, valor, qtd, mi):
        conn = conectar()
        cur = conn.cursor()
        # Remove apenas mensalidades do ano letivo ao salvar novo
        cur.execute("DELETE FROM mensalidades WHERE id_aluno=? AND mes_ano LIKE ?", (self.id_aluno, f"%/{ano}"))

        mes_atual = mi - 1  # índice 0-based
        for i in range(qtd):
            # Calcula mês e ano corretamente, atravessando dezembro → janeiro
            mes = (mes_atual + i) % 12
            deslocamento_ano = (mes_atual + i) // 12
            ano_correto = ano + deslocamento_ano

            mes_ano_str = f"{LISTA_MESES[mes]}/{ano_correto}"
            vencimento_str = f"10/{LISTA_MESES[mes]}/{ano_correto}"

            try:
                cur.execute(
                    "INSERT INTO mensalidades VALUES (NULL,?,?,?,?,NULL,'A Receber')",
                    (self.id_aluno, mes_ano_str, valor, vencimento_str)
                )
            except sqlite3.IntegrityError:
                # Se já existir, ignora sem travar
                pass

        conn.commit()
        conn.close()

    def atualizar_mensalidade(self):
        if not self.id_mensal:
            messagebox.showwarning("Aviso", "Selecione uma mensalidade!")
            return
        try:
            v = float(self.valor_mes.get().replace(',', '.'))
            if v <= 0:
                raise ValueError("Valor negativo")
        except Exception as e:
            messagebox.showwarning("Aviso", f"Valor inválido! {e}")
            return
        ve = self.venc.get().strip()
        st = self.status.get()
        pg = self.data_pag.get().strip() if st == "Quitada" else None
        if st == "Quitada" and not data_valida(pg):
            messagebox.showwarning("Aviso", "Data de pagamento inválida!")
            return
        if not data_valida(ve):
            messagebox.showwarning("Aviso", "Data de vencimento inválida!")
            return
        conn = conectar()
        cur = conn.cursor()
        cur.execute("UPDATE mensalidades SET valor=?, vencimento=?, data_pagamento=?, status=? WHERE id_mensalidade=?",
                    (v, ve, pg, st, self.id_mensal))
        conn.commit()
        conn.close()
        self.carregar_mensalidades()
        messagebox.showinfo("Sucesso", "Mensalidade atualizada!")

    def limpar_campos(self):
        self.id_aluno = None
        self.id_mensal = None
        self.nome.delete(0, tk.END)
        self.resp.delete(0, tk.END)
        self.dt_mat.delete(0, tk.END)
        self.dt_mat.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ano.delete(0, tk.END)
        self.ano.insert(0, str(datetime.now().year))
        self.valor.delete(0, tk.END)
        self.parcelas.delete(0, tk.END)
        self.parcelas.insert(0, "12")
        self.mes_inic.current(0)
        self.turno.current(0)
        self.status.set("A Receber")
        self.mostrar_data_pagamento()
        for i in self.tabela.get_children():
            self.tabela.delete(i)

    def imprimir_aluno(self):
        if not self.id_aluno:
            messagebox.showwarning("Aviso", "Selecione um aluno!")
            return
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT * FROM alunos WHERE id_aluno=?", (self.id_aluno,))
        d = cur.fetchone()
        conn.close()
        txt = (
            f"Nome: {d[1]}\n"
            f"Responsável: {d[2]}\n"
            f"Data Matrícula: {d[3]}\n"
            f"Ano Letivo: {d[4]}\n"
            f"Valor Mensal: {formatar_valor(d[5])}\n"
            f"Total Parcelas: {d[6]}\n"
            f"Mês Inicial: {NOMES_MESES[d[7]-1]}\n"
            f"Turno: {d[8]}"
        )
        Relatorio(self.janela, "FICHA DO ALUNO", txt, f"Matrícula em {d[3]}")

    def imprimir_recibo(self):
        if not self.id_mensal:
            messagebox.showwarning("Aviso", "Selecione uma mensalidade!")
            return
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT a.nome, a.responsavel, m.mes_ano, m.valor, m.vencimento, m.data_pagamento, m.status "
                    "FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno WHERE id_mensalidade=?", (self.id_mensal,))
        d = cur.fetchone()
        conn.close()
        txt = (
            f"Aluno: {d[0]}\n"
            f"Responsável: {d[1]}\n"
            f"Mês/Ano: {d[2]}\n"
            f"Valor: {formatar_valor(d[3])}\n"
            f"Vencimento: {d[4]}\n"
            f"Status: {d[6]}"
        )
        if d[5]:
            txt += f"\nData Pagamento: {d[10]}"
        Relatorio(self.janela, "RECIBO DE MENSALIDADE", txt, d[2])

    # --- RELATÓRIOS ---
    def rel_todos(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT nome, responsavel, ano_letivo, valor_mensal, turno FROM alunos ORDER BY nome")
        d = cur.fetchall()
        conn.close()
        txt = ""
        for n, r, a, v, t in d:
            txt += f"{n:<25} | {r:<20} | {a:<4} | {formatar_valor(v):<12} | {t}\n"
        Relatorio(self.janela, "RELATÓRIO GERAL DE ALUNOS", txt, f"Ano Letivo {datetime.now().year}")

    def rel_a_receber(self):
        conn = conectar()
        cur = conn.cursor()
        hoje = datetime.now().strftime("%d/%m/%Y")
        cur.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno "
                    "WHERE m.status='A Receber' AND m.vencimento>=? ORDER BY m.mes_ano", (hoje,))
        d = cur.fetchall()
        conn.close()
        txt = ""
        total = 0
        for n, m, v, ve in d:
            txt += f"{n:<25} | {m:<8} | {formatar_valor(v):<12} | {ve}\n"
            total += v
        txt += f"\nTOTAL A RECEBER: {formatar_valor(total)}"
        Relatorio(self.janela, "MENSALIDADES A RECEBER", txt, f"Até {hoje}")

    def rel_atrasadas(self):
        conn = conectar()
        cur = conn.cursor()
        hoje = datetime.now().strftime("%d/%m/%Y")
        cur.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno "
                    "WHERE m.status='A Receber' AND m.vencimento<? ORDER BY m.mes_ano", (hoje,))
        d = cur.fetchall()
        conn.close()
        txt = ""
        total = 0
        for n, m, v, ve in d:
            txt += f"{n:<25} | {m:<8} | {formatar_valor(v):<12} | {ve}\n"
            total += v
        txt += f"\nTOTAL ATRASADO: {formatar_valor(total)}"
        Relatorio(self.janela, "MENSALIDADES ATRASADAS", txt, f"Até {hoje}")

    def rel_quitadas(self):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT a.nome, m.mes_ano, m.valor, m.data_pagamento FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno "
                    "WHERE m.status='Quitada' ORDER BY m.mes_ano")
        d = cur.fetchall()
        conn.close()
        txt = ""
        total = 0
        for n, m, v, p in d:
            txt += f"{n:<25} | {m:<8} | {formatar_valor(v):<12} | {p or '-'}\n"
            total += v
        txt += f"\nTOTAL QUITADO: {formatar_valor(total)}"
        Relatorio(self.janela, "MENSALIDADES QUITADAS", txt, f"Período de {datetime.now().year}")

    def rel_periodo(self):
        janela = tk.Toplevel(self.janela)
        janela.title("Relatório por Período e Status")
        janela.geometry("350x280")
        janela.transient(self.janela)
        janela.grab_set()

        ttk.Label(janela, text="Data Inicial (dd/mm/aaaa):").pack(pady=5)
        dt_inicio = ttk.Entry(janela)
        dt_inicio.insert(0, f"01/01/{datetime.now().year}")
        dt_inicio.pack(pady=5)

        ttk.Label(janela, text="Data Final (dd/mm/aaaa):").pack(pady=5)
        dt_fim = ttk.Entry(janela)
        dt_fim.insert(0, datetime.now().strftime("%d/%m/%Y"))
        dt_fim.pack(pady=5)

        ttk.Label(janela, text="Filtrar por Status:").pack(pady=(15, 5))
        filtro_status = ttk.Combobox(janela, values=["Todos", "A Receber", "Atrasadas", "Quitadas"], state="readonly", width=25)
        filtro_status.current(0)
        filtro_status.pack(pady=5)

        def gerar():
            di = dt_inicio.get().strip()
            df = dt_fim.get().strip()
            sts = filtro_status.get()
            if not data_valida(di) or not data_valida(df):
                messagebox.showwarning("Aviso", "Datas inválidas! Use dd/mm/aaaa")
                return

            conn = conectar()
            cur = conn.cursor()
            hoje = datetime.now().strftime("%d/%m/%Y")

            if sts == "Todos":
                cur.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno "
                            "WHERE m.vencimento BETWEEN ? AND ? ORDER BY m.mes_ano, a.nome", (di, df))
                titulo = f"RELATÓRIO GERAL DE {di} A {df}"
            elif sts == "A Receber":
                cur.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno "
                            "WHERE m.status='A Receber' AND m.vencimento BETWEEN ? AND ? AND m.vencimento>=? ORDER BY m.mes_ano, a.nome", (di, df, hoje))
                titulo = f"MENSALIDADES A RECEBER - {di} A {df}"
            elif sts == "Atrasadas":
                cur.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno "
                            "WHERE m.status='A Receber' AND m.vencimento BETWEEN ? AND ? AND m.vencimento<? ORDER BY m.mes_ano, a.nome", (di, df, hoje))
                titulo = f"MENSALIDADES ATRASADAS - {di} A {df}"
            elif sts == "Quitadas":
                cur.execute("SELECT a.nome, m.mes_ano, m.valor, m.vencimento, m.status FROM mensalidades m JOIN alunos a ON m.id_aluno=a.id_aluno "
                            "WHERE m.status='Quitada' AND m.vencimento BETWEEN ? AND ? ORDER BY m.mes_ano, a.nome", (di, df))
                titulo = f"MENSALIDADES QUITADAS - {di} A {df}"
            else:
                return

            d = cur.fetchall()
            conn.close()
            if not d:
                messagebox.showinfo("Aviso", "Nenhum registro encontrado para esse filtro!")
                janela.destroy()
                return
            txt = ""
            total = 0
            for n, m, v, ve, s in d:
                txt += f"{n:<25} | {m:<8} | {formatar_valor(v):<12} | {ve:<10} | {s}\n"
                total += v
            txt += f"\nTOTAL NO PERÍODO: {formatar_valor(total)}"
            Relatorio(self.janela, titulo, txt, f"{di} até {df} | {sts}")
            janela.destroy()

        ttk.Button(janela, text="Gerar Relatório", command=gerar).pack(pady=10)


if __name__ == "__main__":
    janela = tk.Tk()
    app = Sistema(janela)
    janela.mainloop()
