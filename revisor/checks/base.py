"""Formato dos problemas encontrados pelas verificações."""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["alta", "media", "baixa"]
SEVERITIES: tuple[Severity, ...] = ("alta", "media", "baixa")


@dataclass
class Finding:
    """Um problema metodológico localizado no código.

    `cell` é o índice da célula e `line` a linha dentro dela.
    `severity` é "alta", "media" ou "baixa".
    """

    check: str
    cell: int
    line: int
    snippet: str
    severity: Severity
    message: str

    def __post_init__(self) -> None:
        if self.severity not in SEVERITIES:
            raise ValueError(f"gravidade inválida: {self.severity}")
