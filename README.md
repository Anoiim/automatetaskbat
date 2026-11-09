# 🕒 BAT Scheduler

> **Nasceu para automatizar tarefas em servidores lagados** — porque ninguém
> merece abrir o Agendador de Tarefas do Windows, brigar com uma UI confusa
> e ainda descobrir que a tarefa simplesmente *não rodou*.

Interface gráfica simples para agendar a execução de scripts `.bat` em
horários e dias específicos, **sem depender do Agendador de Tarefas do
Windows**.

---

## 🎯 Por que este projeto existe?

O **Agendador de Tarefas do Windows** é notoriamente problemático:

- ❌ Falha silenciosamente — a tarefa está "agendada", mas nunca executa;
- ❌ Interface confusa e cheia de menus escondidos;
- ❌ Exige configurações obscuras de permissões e contexto de usuário;
- ❌ Difícil de usar para agendar **scripts `.bat` simples**.

O **BAT Scheduler** resolve isso com uma janela única:

1. Escolha o arquivo `.bat`
2. Defina o horário (`HH:MM`)
3. Marque os dias da semana
4. Clique em **Agendar**

Pronto. Sem mistério, sem "Executar como administrador", sem surpresas.

---

## ✨ Funcionalidades

- 📂 **Seleção visual** de arquivo `.bat`
- 🕐 **Agendamento por horário** com validação de formato
- 📅 **Seleção de dias da semana** com checkboxes
- 💾 **Persistência em `agendamentos.json`** — sobrevive a fechamentos
- 🗑️ **Remoção de agendamentos** diretamente na tabela
- 📋 **Coluna "Última execução"** — saiba quando cada job rodou
- 📜 **Log em painel + arquivo** (`execucoes.log`)
- ⚡ **Thread worker única** — sem threads duplicadas, sem UI travada
- 🌎 **Locale-independent** — usa `weekday()` numérico, funciona em pt-BR
- 🪶 **Zero dependências externas** — só Python padrão

---

