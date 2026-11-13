# Passo a passo: projeto com o Cursor

## Primeira vez (só uma vez neste projeto)

1. **Abra a pasta no Cursor:** File → Open Folder → `Documentos\revisor-ml`.
2. **Abra o terminal do Cursor:** Ctrl+' (aspas simples) ou menu Terminal → New Terminal.
3. **Crie e ative o ambiente virtual:**
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
   Vai aparecer `(.venv)` no começo da linha. Toda vez que abrir um terminal novo, rode o `activate` de novo.
   Se o PowerShell bloquear, rode antes: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` e confirme com S.
4. **Escolha o interpretador:** Ctrl+Shift+P → "Python: Select Interpreter" → o que tem `.venv`.
5. **Inicie o git:**
   ```
   git init
   git add .
   git commit -m "estrutura inicial e regras do Cursor"
   ```
6. **Crie o repositório no GitHub:** github.com/new → nome `revisor-ml`, público, **sem** README (já temos um).
   Depois, no terminal:
   ```
   git remote add origin https://github.com/elleoliveir/revisor-ml.git
   git branch -M main
   git push -u origin main
   ```
7. **Confira o Ollama:** o app do Ollama precisa estar aberto (ícone perto do relógio).

## A cada etapa

1. Abra o chat do Cursor no modo **Agent** (Ctrl+I).
2. Copie o prompt da etapa em `PROMPTS.md` e cole.
3. O Cursor mostra cada arquivo alterado em verde e vermelho. **Leia antes de aceitar.** Se não entender uma parte,
   selecione o trecho e pergunte "explique esta parte" (Ctrl+L).
4. Aceite (Accept) o que estiver certo; recuse (Reject) e peça ajuste no que não estiver.
5. Rode os testes: `pytest`. Tudo precisa passar.
6. Faça o commit e envie:
   ```
   git add .
   git commit -m "mensagem da etapa"
   git push
   ```
7. Anote em `DECISOES.md` qualquer escolha que você fez e por quê.

Dica: se o Cursor começar a mexer em coisas que você não pediu, clique em Reject All e repita o pedido
dizendo exatamente quais arquivos ele pode alterar.

## Para fazer sozinha num próximo projeto

1. **Planeje antes de abrir o Cursor.** Escreva numa página: o que o sistema faz, a stack, a estrutura de pastas
   e a lista de etapas. Cada etapa deve caber em um pedido e terminar com algo testável.
2. **Crie o arquivo de regras** em `.cursor/rules/projeto.mdc`, como o deste projeto: o que é o projeto, a stack,
   a estrutura e "como trabalhar comigo". Assim o Cursor recebe esse contexto em todo pedido, e você não precisa repetir.
3. **Escreva prompts bons.** Um prompt bom diz:
   - **qual arquivo** criar ou alterar (`revisor/checks/missing_seed.py`);
   - **qual função**, com nome e o que recebe e devolve (`check(cells) -> list[Finding]`);
   - **o comportamento esperado**, com exemplos de quando deve e quando não deve disparar;
   - **os testes** que quer;
   - **o limite** ("não crie mais nada além disso").
4. **Uma etapa por vez, sempre com teste e commit.** Pedir "faça o projeto inteiro" gera código que você não consegue
   explicar numa entrevista.
5. **Quando der erro**, cole a mensagem de erro inteira no chat do Cursor e peça para ele explicar a causa antes de corrigir.
