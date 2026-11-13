"""Confere a conexão com o modelo local fazendo uma pergunta curta."""

from revisor.llm import get_llm

QUESTION = "Responda em uma frase: o que é vazamento de dados em machine learning?"


def main() -> None:
    """Pergunta ao modelo o que é vazamento de dados e imprime a resposta."""
    response = get_llm().invoke(QUESTION)
    print(response.content)


if __name__ == "__main__":
    main()
