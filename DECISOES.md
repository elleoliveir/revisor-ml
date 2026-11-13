# Decisões do projeto

Anote aqui cada decisão importante e o porquê. Isso vira material para o README e para entrevistas.

| Data | Decisão | Por quê |
|---|---|---|
| | Regras determinísticas + LLM, em vez de só LLM | As regras são reproduzíveis e testáveis; o LLM entra para interpretar e explicar |
| | LangGraph para orquestrar os agentes | Deixa o fluxo entre agentes explícito no código, com estado |
| | Ollama local (qwen2.5:7b) | Sem custo, coerente com meus outros projetos; dá para trocar por API |
