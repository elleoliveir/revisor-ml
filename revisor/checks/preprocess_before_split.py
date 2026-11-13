"""Detecta pré-processamento ajustado antes do train_test_split."""

import ast
from dataclasses import dataclass

from revisor.checks.base import Finding
from revisor.parser import Cell, _expr_name, _import_aliases

CHECK = "preprocess_before_split"
SCALER_CLASSES = {"StandardScaler", "MinMaxScaler", "PCA", "SimpleImputer"}
FIT_METHODS = {"fit", "fit_transform"}
IGNORED_SPLIT_KEYWORDS = {"test_size", "train_size", "random_state", "shuffle", "stratify"}


@dataclass
class _Fit:
    """Ajuste de um pré-processador e as variáveis que ele contamina."""

    order: int
    cell: int
    line: int
    column: int
    code: str
    class_name: str
    method: str
    variables: list[str]

    def position(self) -> tuple[int, int, int]:
        return (self.order, self.line, self.column)


@dataclass
class _Split:
    """Uma chamada de train_test_split e as variáveis que ela divide."""

    order: int
    line: int
    column: int
    variables: set[str]

    def position(self) -> tuple[int, int, int]:
        return (self.order, self.line, self.column)


def check(cells: list[Cell]) -> list[Finding]:
    """Aponta StandardScaler, MinMaxScaler, PCA ou SimpleImputer ajustados cedo demais.

    O ajuste conta quando `fit` ou `fit_transform` usa uma variável, ou produz
    outra, antes da célula ou da linha em que essa variável entra no
    `train_test_split`. A gravidade é alta.
    """
    known: dict[str, str] = {}
    fits: list[_Fit] = []
    splits: list[_Split] = []
    for order, cell in enumerate(cells):
        try:
            tree = ast.parse(cell.code)
        except SyntaxError:
            continue
        visitor = _Visitor(
            aliases=_import_aliases(tree),
            known=known,
            order=order,
            cell_index=cell.index,
            code=cell.code,
            fits=fits,
            splits=splits,
        )
        visitor.visit(tree)

    findings: list[Finding] = []
    for fit in fits:
        matched = _matched_variables(fit, splits)
        if matched:
            findings.append(_to_finding(fit, matched))
    return findings


def _matched_variables(fit: _Fit, splits: list[_Split]) -> list[str]:
    """Variáveis deste ajuste que são divididas numa posição posterior."""
    matched: list[str] = []
    for variable in fit.variables:
        if variable in matched:
            continue
        if any(variable in split.variables and fit.position() < split.position() for split in splits):
            matched.append(variable)
    return matched


def _to_finding(fit: _Fit, variables: list[str]) -> Finding:
    """Monta o achado de gravidade alta para um ajuste feito cedo demais."""
    names = ", ".join(f"`{name}`" for name in variables)
    return Finding(
        check=CHECK,
        cell=fit.cell,
        line=fit.line,
        snippet=_snippet(fit.code, fit.line),
        severity="alta",
        message=(
            f"{fit.class_name}.{fit.method} acontece antes do train_test_split de {names}. "
            "Assim o teste influencia o pré-processamento. "
            f"Divida os dados antes e ajuste o {fit.class_name} só com o treino."
        ),
    )


def _snippet(code: str, line: int) -> str:
    """Devolve o texto da linha citada, sem espaços nas pontas."""
    lines = code.splitlines()
    if 1 <= line <= len(lines):
        return lines[line - 1].strip()
    return ""


def _constructor_class(node: ast.AST, aliases: dict[str, str]) -> str | None:
    """Reconhece o construtor de um dos pré-processadores vigiados."""
    if not isinstance(node, ast.Call):
        return None
    class_name = _expr_name(node.func, aliases).split(".")[-1]
    if class_name in SCALER_CLASSES:
        return class_name
    return None


def _fitted_variable(node: ast.Call) -> str | None:
    """Nome da variável passada como dados para fit ou fit_transform."""
    if node.args and isinstance(node.args[0], ast.Name):
        return node.args[0].id
    for keyword in node.keywords:
        if keyword.arg == "X" and isinstance(keyword.value, ast.Name):
            return keyword.value.id
    return None


def _split_variables(node: ast.Call) -> list[str]:
    """Nomes divididos por train_test_split, ignorando argumentos de controle."""
    found: list[str] = []
    for arg in node.args:
        if isinstance(arg, ast.Name) and arg.id not in found:
            found.append(arg.id)
    for keyword in node.keywords:
        if keyword.arg in IGNORED_SPLIT_KEYWORDS or keyword.arg is None:
            continue
        if isinstance(keyword.value, ast.Name) and keyword.value.id not in found:
            found.append(keyword.value.id)
    return found


def _is_split(node: ast.Call, aliases: dict[str, str]) -> bool:
    """Diz se a chamada é train_test_split, mesmo com o módulo resolvido."""
    name = _expr_name(node.func, aliases)
    return name == "train_test_split" or name.endswith(".train_test_split")


class _Visitor(ast.NodeVisitor):
    """Percorre o código na ordem em que as células seriam executadas."""

    def __init__(
        self,
        aliases: dict[str, str],
        known: dict[str, str],
        order: int,
        cell_index: int,
        code: str,
        fits: list[_Fit],
        splits: list[_Split],
    ) -> None:
        self.aliases = aliases
        self.known = known
        self.order = order
        self.cell_index = cell_index
        self.code = code
        self.fits = fits
        self.splits = splits

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Ignora funções: a ordem das linhas lá dentro não é a ordem de execução."""
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Ignora funções assíncronas, pelo mesmo motivo de visit_FunctionDef."""
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Ignora o corpo de classes."""
        return

    def visit_Assign(self, node: ast.Assign) -> None:
        before = len(self.fits)
        self.generic_visit(node)
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        if not names or len(names) != len(node.targets):
            return

        class_name = _constructor_class(node.value, self.aliases)
        if class_name:
            for name in names:
                self.known[name] = class_name
            return

        if len(names) == 1 and len(self.fits) == before + 1:
            fit = self.fits[-1]
            if fit.method == "fit":
                self.known[names[0]] = fit.class_name
                return
            if names[0] not in fit.variables:
                fit.variables.append(names[0])

        if len(names) == 1 and isinstance(node.value, ast.Name) and node.value.id in self.known:
            self.known[names[0]] = self.known[node.value.id]
            return

        for name in names:
            self.known.pop(name, None)

    def visit_Call(self, node: ast.Call) -> None:
        self._record_fit(node)
        self._record_split(node)
        self.generic_visit(node)

    def _record_fit(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Attribute) or node.func.attr not in FIT_METHODS:
            return
        variable = _fitted_variable(node)
        if variable is None:
            return
        class_name = _constructor_class(node.func.value, self.aliases)
        if class_name is None and isinstance(node.func.value, ast.Name):
            class_name = self.known.get(node.func.value.id)
        if class_name is None:
            return
        self.fits.append(
            _Fit(
                order=self.order,
                cell=self.cell_index,
                line=node.lineno,
                column=node.col_offset,
                code=self.code,
                class_name=class_name,
                method=node.func.attr,
                variables=[variable],
            )
        )

    def _record_split(self, node: ast.Call) -> None:
        if not _is_split(node, self.aliases):
            return
        variables = _split_variables(node)
        if not variables:
            return
        self.splits.append(
            _Split(
                order=self.order,
                line=node.lineno,
                column=node.col_offset,
                variables=set(variables),
            )
        )
