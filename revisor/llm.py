"""Conexão com o modelo local via Ollama."""

import os

from langchain_ollama import ChatOllama

DEFAULT_MODEL = "qwen2.5:7b"


def get_llm() -> ChatOllama:
    """Devolve um chat do Ollama com o modelo de REVISOR_MODEL.

    Se a variável de ambiente não estiver definida, usa qwen2.5:7b.
    """
    model = os.environ.get("REVISOR_MODEL", DEFAULT_MODEL)
    return ChatOllama(model=model)
