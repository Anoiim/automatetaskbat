import tkinter as tk
from tkinter import filedialog, messagebox
import datetime
import time
import threading
import os


# Função para escolher o arquivo BAT
def escolher_arquivo():
    caminho_arquivo.set(filedialog.askopenfilename(filetypes=[("Arquivos BAT", "*.bat")]))


# Função para rodar o BAT na hora certa
def agendar_execucao():
    arquivo = caminho_arquivo.get()
    horario = horario_entrada.get()
    dias_selecionados = [dias[i] for i in range(7) if dias_vars[i].get()]

    if not arquivo:
        messagebox.showerror("Erro", "Escolha um arquivo BAT.")
        return

    if not horario:
        messagebox.showerror("Erro", "Informe um horário.")
        return

    if not dias_selecionados:
        messagebox.showerror("Erro", "Escolha pelo menos um dia.")
        return

    agendamento = f"{arquivo} às {horario} nos dias: {', '.join(dias_selecionados)}"
    lista_agendamentos.insert(tk.END, agendamento)
    messagebox.showinfo("Agendado",
                        f"O arquivo {arquivo} foi agendado para execução às {horario} nos dias: {', '.join(dias_selecionados)}.")

    def verificar_execucao():
        while True:
            agora = datetime.datetime.now()
            dia_atual = agora.strftime("%A")
            hora_atual = agora.strftime("%H:%M")

            if dia_atual in dias_selecionados and hora_atual == horario:
                os.system(f'start "" "{arquivo}"')
                time.sleep(60)  # Espera 1 minuto para evitar execuções múltiplas no mesmo minuto

            time.sleep(10)  # Verifica a cada 10 segundos

    threading.Thread(target=verificar_execucao, daemon=True).start()


# Criando interface
dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
root = tk.Tk()
root.title("Agendador de BAT")
root.geometry("600x300")
root.resizable(False, False)

caminho_arquivo = tk.StringVar()
dias_vars = [tk.IntVar() for _ in range(7)]

# Centralizando os elementos
frame = tk.Frame(root)
frame.pack(expand=True)

# Botão para selecionar arquivo
btn_escolher = tk.Button(frame, text="Escolher Arquivo BAT", command=escolher_arquivo)
btn_escolher.pack()

# Campo para exibir caminho do arquivo
lbl_caminho = tk.Label(frame, textvariable=caminho_arquivo)
lbl_caminho.pack()

# Entrada de horário
lbl_horario = tk.Label(frame, text="Horário (HH:MM):")
lbl_horario.pack()
horario_entrada = tk.Entry(frame)
horario_entrada.pack()

# Checkboxes para dias da semana
lbl_dias = tk.Label(frame, text="Escolha os dias:")
lbl_dias.pack()

dias_frame = tk.Frame(frame)
dias_frame.pack()

for i, dia in enumerate(dias):
    chk = tk.Checkbutton(dias_frame, text=dia, variable=dias_vars[i])
    chk.grid(row=0, column=i, padx=2)

# Botão para agendar execução
btn_agendar = tk.Button(frame, text="Agendar Execução", command=agendar_execucao)
btn_agendar.pack()

# Lista para mostrar tarefas agendadas
lbl_agendamentos = tk.Label(frame, text="Tarefas Agendadas:")
lbl_agendamentos.pack()
lista_agendamentos = tk.Listbox(frame, height=5, width=40)
lista_agendamentos.pack()

root.mainloop()
