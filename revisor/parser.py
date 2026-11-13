"""Le scripts e notebooks e extrai as chamadas de função de cada célula."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Call:
    """Chamada de função encontrada no código de uma célula."""

    name: str
    line: int


@dataclass
class Cell:
    """Célula de código com as chamadas que o parser conseguiu ler.

    Em notebooks, `index` é a posição da célula no arquivo, contando markdown.
    Em scripts, há uma única célula e `index` é 0.
    """

    index: int
    code: str
    calls: list[Call]


def load_cells(path: str | Path) -> list[Cell]:
    """Lê um `.py` ou `.ipynb` e devolve as células de código.

    Notebooks ignoram células de markdown. Um script vira uma célula só.
    Célula com erro de sintaxe volta sem chamadas.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".py":
        code = file_path.read_text(encoding="utf-8")
        return [_make_cell(0, code)]
    if suffix == ".ipynb":
        return _load_notebook(file_path)
    raise ValueError(f"formato não suportado: {file_path.suffix}")


def _load_notebook(path: Path) -> list[Cell]:
    """Lê as células de código de um notebook, preservando o índice original."""
    import nbformat

    notebook = nbformat.read(path, as_version=4)
    cells: list[Cell] = []
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        source = cell.source
        if isinstance(source, list):
            source = "".join(source)
        cells.append(_make_cell(index, source))
    return cells


def _make_cell(index: int, code: str) -> Cell:
    """Monta uma célula e preenche as chamadas quando o código é válido."""
    return Cell(index=index, code=code, calls=_find_calls(code))


def _find_calls(code: str) -> list[Call]:
    """Lista as chamadas na ordem do código, com o nome resolvido pelos imports."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    aliases = _import_aliases(tree)
    visitor = _CallVisitor(aliases)
    visitor.visit(tree)
    return visitor.calls


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    """Mapeia o nome local de cada import para o caminho completo do módulo."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    aliases[root] = root
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                prefix = "." * node.level + node.module
            else:
                prefix = "." * node.level
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                qualified = f"{prefix}.{alias.name}" if prefix else alias.name
                aliases[local] = qualified
    return aliases


def _expr_name(node: ast.AST, aliases: dict[str, str]) -> str:
    """Reconstrói o nome de uma expressão, trocando aliases de import."""
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        prefix = _expr_name(node.value, aliases)
        if prefix:
            return f"{prefix}.{node.attr}"
        return node.attr
    if isinstance(node, ast.Call):
        return _expr_name(node.func, aliases)
    return ast.unparse(node)


class _CallVisitor(ast.NodeVisitor):
    """Percorre a árvore e guarda cada chamada com a linha."""

    def __init__(self, aliases: dict[str, str]) -> None:
        self.aliases = aliases
        self.calls: list[Call] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = _expr_name(node.func, self.aliases)
        if name:
            self.calls.append(Call(name=name, line=node.lineno))
        self.generic_visit(node)
