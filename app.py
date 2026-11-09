import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import datetime
import threading
import json
import os
import re
import sys
import uuid


# ---------- Configuração de caminhos ----------
if getattr(sys, "frozen", False):          # rodando como .exe (PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCHEDULES_FILE = os.path.join(BASE_DIR, "agendamentos.json")
LOG_FILE = os.path.join(BASE_DIR, "execucoes.log")

# Dias: 0=Segunda ... 6=Domingo (padrão datetime.weekday())
DIAS_PT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


# ============================================================
#  Agendador (lógica separada da UI)
# ============================================================
class Scheduler:
    """Gerencia agendamentos, persistência e execução em background."""

    def __init__(self, on_log=None):
        self.jobs: list[dict] = []
        self.lock = threading.Lock()
        self.on_log = on_log or (lambda msg: None)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._load()

    # ---------- persistência ----------
    def _load(self):
        if not os.path.exists(SCHEDULES_FILE):
            return
        try:
            with open(SCHEDULES_FILE, "r", encoding="utf-8") as f:
                self.jobs = json.load(f)
            self.on_log(f"[OK] {len(self.jobs)} agendamento(s) carregado(s).")
        except Exception as e:
            self.on_log(f"[ERRO] Falha ao carregar agendamentos: {e}")
            self.jobs = []

    def _save(self):
        try:
            with open(SCHEDULES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.jobs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.on_log(f"[ERRO] Falha ao salvar: {e}")

    # ---------- API pública ----------
    def add(self, arquivo: str, horario: str, dias: list[int]):
        if not TIME_RE.match(horario):
            raise ValueError("Horário inválido. Use o formato HH:MM (ex: 14:30).")
        if not dias:
            raise ValueError("Selecione pelo menos um dia da semana.")
        if not arquivo or not os.path.isfile(arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {arquivo!r}")

        job = {
            "id": str(uuid.uuid4()),
            "arquivo": arquivo,
            "horario": horario,
            "dias": sorted(dias),
            "ultima_execucao": None,
        }
        with self.lock:
            self.jobs.append(job)
            self._save()
        self.on_log(f"[OK] Agendado: {os.path.basename(arquivo)} às {horario}")
        return job

    def remove(self, job_id: str):
        with self.lock:
            antes = len(self.jobs)
            self.jobs = [j for j in self.jobs if j["id"] != job_id]
            if len(self.jobs) < antes:
                self._save()
                self.on_log("[OK] Agendamento removido.")

    def list(self) -> list[dict]:
        """Retorna cópias para evitar race condition com o worker."""
        with self.lock:
            return [dict(j) for j in self.jobs]

    # ---------- worker ----------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.on_log("[OK] Worker iniciado.")

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:
                self.on_log(f"[ERRO] Worker: {e}")
            self._stop.wait(5)          # checa a cada 5 segundos

    def _tick(self):
        now = datetime.datetime.now()
        chave_minuto = now.strftime("%Y-%m-%d %H:%M")
        hora_atual = now.strftime("%H:%M")
        dia_atual = now.weekday()      # 0=Seg ... 6=Dom (independente de locale)

        disparar = []
        with self.lock:
            for job in self.jobs:
                if dia_atual not in job["dias"]:
                    continue
                if job["horario"] != hora_atual:
                    continue
                if job["ultima_execucao"] == chave_minuto:
                    continue
                job["ultima_execucao"] = chave_minuto
                disparar.append(job)
            if disparar:
                self._save()

        for job in disparar:
            try:
                os.startfile(job["arquivo"])          # equivalente a duplo-clique
                self.on_log(f"[RUN] {os.path.basename(job['arquivo'])} → {chave_minuto}")
            except FileNotFoundError:
                self.on_log(f"[ERRO] Arquivo sumiu: {job['arquivo']}")
            except Exception as e:
                self.on_log(f"[ERRO] Falha ao executar {job['arquivo']}: {e}")


# ============================================================
#  Interface
# ============================================================
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BAT Scheduler")
        self.root.geometry("760x600")
        self.root.minsize(720, 560)

        self.scheduler = Scheduler(on_log=self.log)
        self.caminho_arquivo = tk.StringVar()
        self.horario_var = tk.StringVar()
        self.dias_vars = [tk.IntVar() for _ in range(7)]

        self._build_ui()
        self._refresh_list()
        self.scheduler.start()
        self._auto_refresh()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- construção ----------
    def _build_ui(self):
        # 1) Arquivo
        f_arq = tk.LabelFrame(self.root, text="1) Arquivo .BAT", padx=8, pady=8)
        f_arq.pack(fill="x", padx=10, pady=(10, 5))
        tk.Button(f_arq, text="📂 Escolher Arquivo", command=self.escolher_arquivo).pack(side="left")
        tk.Label(f_arq, textvariable=self.caminho_arquivo, anchor="w",
                 fg="#666").pack(side="left", padx=8, fill="x", expand=True)

        # 2) Quando executar
        f_ag = tk.LabelFrame(self.root, text="2) Quando executar", padx=8, pady=8)
        f_ag.pack(fill="x", padx=10, pady=5)

        row = tk.Frame(f_ag); row.pack(fill="x")
        tk.Label(row, text="Horário (HH:MM):").pack(side="left")
        tk.Entry(row, textvariable=self.horario_var, width=8).pack(side="left", padx=5)
        tk.Label(row, text="ex: 14:30", fg="#888").pack(side="left")

        row2 = tk.Frame(f_ag); row2.pack(fill="x", pady=(8, 0))
        tk.Label(row2, text="Dias:").pack(side="left")
        for i, dia in enumerate(DIAS_PT):
            tk.Checkbutton(row2, text=dia, variable=self.dias_vars[i]).pack(side="left", padx=2)

        tk.Button(f_ag, text="➕ Agendar Execução", command=self.agendar,
                  bg="#4CAF50", fg="white", font=("Segoe UI", 9, "bold")).pack(pady=(8, 0))

        # 3) Lista de agendamentos
        f_lista = tk.LabelFrame(self.root, text="3) Agendamentos", padx=8, pady=8)
        f_lista.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("arquivo", "horario", "dias", "ultima")
        self.tree = ttk.Treeview(f_lista, columns=cols, show="headings", height=6)
        for c, txt, w, anchor in [
            ("arquivo", "Arquivo", 300, "w"),
            ("horario", "Horário", 70, "center"),
            ("dias", "Dias", 160, "center"),
            ("ultima", "Última execução", 140, "center"),
        ]:
            self.tree.heading(c, text=txt)
            self.tree.column(c, width=w, anchor=anchor)
        self.tree.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(f_lista, orient="vertical", command=self.tree.yview)
        sb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        tk.Button(f_lista, text="🗑 Remover", command=self.remover,
                  bg="#e53935", fg="white").pack(side="right", padx=(5, 0), fill="y")

        # 4) Log
        f_log = tk.LabelFrame(self.root, text="Log de execução", padx=8, pady=8)
        f_log.pack(fill="both", padx=10, pady=(5, 10))
        self.log_text = tk.Text(f_log, height=7, state="disabled",
                                bg="#1e1e1e", fg="#d4d4d4",
                                font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)

    # ---------- handlers ----------
    def escolher_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos BAT", "*.bat")])
        if caminho:
            self.caminho_arquivo.set(caminho)

    def agendar(self):
        arquivo = self.caminho_arquivo.get().strip()
        horario = self.horario_var.get().strip()
        dias = [i for i in range(7) if self.dias_vars[i].get()]
        try:
            self.scheduler.add(arquivo, horario, dias)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self._refresh_list()
        messagebox.showinfo("Agendado",
                            f"{os.path.basename(arquivo)} agendado para {horario}.")

    def remover(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um agendamento para remover.")
            return
        if messagebox.askyesno("Confirmar", "Remover este agendamento?"):
            self.scheduler.remove(sel[0])
            self._refresh_list()

    # ---------- helpers ----------
    def _refresh_list(self):
        sel = set(self.tree.selection())
        for item in self.tree.get_children():
            self.tree.delete(item)
        for job in self.scheduler.list():
            dias_str = ", ".join(DIAS_PT[d] for d in job["dias"])
            self.tree.insert(
                "", "end", iid=job["id"],
                values=(os.path.basename(job["arquivo"]),
                        job["horario"], dias_str,
                        job.get("ultima_execucao") or "—")
            )
        for iid in sel:
            if self.tree.exists(iid):
                self.tree.selection_add(iid)

    def _auto_refresh(self):
        self._refresh_list()
        self.root.after(3000, self._auto_refresh)

    def log(self, msg: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        linha = f"[{ts}] {msg}"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", linha + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        # grava também em arquivo
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(linha + "\n")
        except Exception:
            pass

    def _on_close(self):
        self.scheduler.stop()
        self.root.destroy()


# ============================================================
if __name__ == "__main__":
    if sys.platform != "win32":
        print("⚠️  Este software foi feito para Windows (usa os.startfile).")
    root = tk.Tk()
    App(root)
    root.mainloop()