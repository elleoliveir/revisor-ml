# Prompts para o Cursor: Revisor de pipelines de ML

Cole um prompt por vez no chat do Cursor, no modo **Agent** (Ctrl+I).
Depois de cada etapa: leia o código, rode `pytest`, faça o commit e só então siga para a próxima.
Se travar ou o resultado ficar estranho, me chame aqui no Claude que eu reviso com você.

---

## Etapa 1: Configuração

> Crie a estrutura inicial do projeto, seguindo as regras em `.cursor/rules/projeto.mdc`:
> pastas `revisor/`, `revisor/checks/`, `eval/notebooks/` e `tests/`, com `__init__.py` onde for pacote Python.
> Crie também `revisor/llm.py` com uma função `get_llm()` que devolve um `ChatOllama` (do pacote `langchain-ollama`)
> usando o modelo da variável de ambiente `REVISOR_MODEL` (padrão `qwen2.5:7b`), e um script `hello_llm.py`
> na raiz que pergunta ao modelo "Responda em uma frase: o que é vazamento de dados em machine learning?" e imprime a resposta.
> Adicione `langchain-ollama` ao `requirements.txt`. Não crie mais nada além disso.

Depois, no terminal do Cursor:
```
ollama pull qwen2.5:7b
pip install -r requirements.txt
python hello_llm.py
```
Commit: `configura projeto e conexão com o Ollama`

---

## Etapa 2: Parser

> Crie `revisor/parser.py` com uma função `load_cells(path)` que aceite `.py` e `.ipynb`.
> Para notebooks, use `nbformat` e ignore células de markdown. Um arquivo `.py` vira uma única célula.
> Para cada célula, devolva um dataclass `Cell` com o índice, o código e a lista de chamadas de função encontradas
> com o módulo `ast` (nome completo quando der para resolver pelos imports, como
> `sklearn.model_selection.train_test_split`, e a linha). Células com erro de sintaxe não devem quebrar o parser:
> devolva a célula sem chamadas. Escreva testes em `tests/test_parser.py` usando arquivos de exemplo
> criados em `tests/fixtures/`.

Commit: `adiciona parser de notebooks e scripts`

---

## Etapa 3a: Formato dos achados + primeira verificação

> Crie `revisor/checks/base.py` com um dataclass `Finding(check, cell, line, snippet, severity, message)`,
> em que `severity` é "alta", "media" ou "baixa".
> Depois crie `revisor/checks/preprocess_before_split.py` com a função `check(cells) -> list[Finding]`.
> A verificação deve detectar quando um objeto com `fit` ou `fit_transform` (StandardScaler, MinMaxScaler,
> PCA, SimpleImputer) é ajustado com uma variável antes da célula ou linha em que essa variável é dividida
> com `train_test_split`. Gravidade alta. Inclua testes com um caso positivo e um negativo.

Commit: `adiciona verificação de pré-processamento antes do split`

## Etapa 3b: Teste usado para ajustar hiperparâmetros ou limiar

> Crie `revisor/checks/test_set_tuning.py`, no mesmo formato de `preprocess_before_split.py`.
> Ela deve detectar o uso de variáveis de teste (`X_test`, `y_test` e nomes parecidos) dentro de
> `GridSearchCV`/`RandomizedSearchCV`/`cross_val_score`, dentro de laços que testam vários valores de
> hiperparâmetro, ou no cálculo de um limiar (por exemplo, `np.percentile` sobre scores de teste). Gravidade alta.
> Testes com caso positivo e negativo.

Commit: `adiciona verificação de uso do teste no ajuste`

## Etapa 3c: Falta de seed

> Crie `revisor/checks/missing_seed.py`, no mesmo formato. Ela deve apontar chamadas a `train_test_split`,
> modelos do scikit-learn que aceitam `random_state` e funções de `np.random` quando não há `random_state`
> nem uma seed definida antes (`np.random.seed`, `random.seed`). Gravidade média.
> Crie também `revisor/checks/__init__.py` com uma lista `ALL_CHECKS` e uma função `run_all(cells)`. Testes.

Commit: `adiciona verificação de seed e execução de todas as verificações`

---

## Etapa 4: Conjunto de avaliação

> Em `eval/notebooks/`, crie 15 notebooks curtos (.ipynb) que treinam modelos com datasets do próprio
> scikit-learn (iris, breast_cancer, wine, digits). Faça 5 corretos e 10 com erros plantados de propósito,
> distribuídos entre: pré-processamento antes do split, teste usado no ajuste, falta de seed.
> Alguns podem ter mais de um erro. Crie `eval/gabarito.json` com, para cada arquivo, a lista de verificações
> que devem disparar e a célula de cada erro. Não rode os notebooks; só crie os arquivos.

**Importante:** abra alguns notebooks e confira se os erros estão onde o gabarito diz. Este conjunto é o que
dá credibilidade aos seus números, então revise com calma.

Commit: `adiciona conjunto de avaliação com gabarito`

---

## Etapa 5: Agentes com LangGraph

> Usando LangGraph, crie `revisor/graph.py` com um grafo de 4 nós: planner, tools, reviewer e writer.
> O estado do grafo guarda as células, os achados e o relatório.
> - planner: recebe um resumo das células e decide quais verificações de `revisor/checks` rodar.
> - tools: roda as verificações escolhidas (código Python normal, sem LLM).
> - reviewer: recebe cada achado com o código ao redor, marca falsos positivos e pode acrescentar
>   observações que as regras não pegam, sempre citando a célula.
> - writer: monta o texto final.
> Use `get_llm()` de `revisor/llm.py`. Coloque os prompts em `revisor/prompts.py`.
> Adicione `langgraph` ao `requirements.txt`. Crie `revisar.py` na raiz que recebe o caminho de um arquivo
> e imprime o relatório. Escreva testes que rodem o grafo com um LLM falso (mock), para não depender do Ollama.

Commit: `adiciona grafo de agentes com LangGraph`

---

## Etapa 6: Relatório

> Crie `revisor/report.py` com `build_report(findings, review_notes) -> str` que gera Markdown com:
> um resumo (quantos problemas por gravidade), os achados ordenados por gravidade, e para cada um
> a célula, a linha, o trecho de código, a explicação e uma sugestão de correção. Use essa função no nó writer.
> Testes.

Commit: `adiciona geração do relatório em Markdown`

---

## Etapa 7: Medir

> Crie `eval/run_eval.py` que roda o revisor em cada notebook de `eval/notebooks`, compara com
> `eval/gabarito.json` e imprime, por verificação, verdadeiros positivos, falsos positivos e falsos negativos,
> com precisão e recall, para dois modos: só regras e regras + LLM (achados que o reviewer descartou
> não contam). Salve a tabela também em `eval/resultados.md`.

Rode `python eval/run_eval.py` e guarde os números. Eles vão para o README e para o currículo.

Commit: `adiciona avaliação e resultados`

---

## Etapa 8: Interface

> Crie `app.py` com Streamlit: upload de um `.ipynb` ou `.py`, um botão "Revisar", uma opção para escolher
> "só regras" ou "regras + LLM", e o relatório em Markdown na tela, com botão para baixar.
> Adicione `streamlit` ao `requirements.txt`.

Rode com `streamlit run app.py`.

Commit: `adiciona interface com Streamlit`

---

## Etapa 9: README

> Reescreva o `README.md` com: o problema (por que vazamento de dados e falta de seed importam), a arquitetura
> (diagrama em texto do grafo), como instalar e rodar, a tabela de `eval/resultados.md`, e uma seção de
> limitações honesta, citando onde o sistema ainda erra. Use as decisões de `DECISOES.md`.
> Não invente números: use só os de `eval/resultados.md`.

Revise o texto você mesma antes de publicar. Me mande que eu dou uma olhada também.

Commit: `escreve README`
