"""Testes da verificação de pré-processamento antes do split."""

from pathlib import Path

import pytest

from revisor.checks.preprocess_before_split import check
from revisor.parser import Cell, load_cells

FIXTURES = Path(__file__).parent / "fixtures"


def _cell(index: int, code: str) -> Cell:
    return Cell(index=index, code=code, calls=[])


@pytest.mark.parametrize(
    ("class_name", "import_line"),
    [
        ("StandardScaler", "from sklearn.preprocessing import StandardScaler"),
        ("MinMaxScaler", "from sklearn.preprocessing import MinMaxScaler"),
        ("PCA", "from sklearn.decomposition import PCA"),
        ("SimpleImputer", "from sklearn.impute import SimpleImputer"),
    ],
)
def test_fit_before_split_of_same_variable_is_high(class_name, import_line):
    code = "\n".join(
        [
            import_line,
            "from sklearn.model_selection import train_test_split",
            f"scaler = {class_name}()",
            "scaler.fit_transform(X)",
            "train_test_split(X, y)",
        ]
    )

    findings = check([_cell(0, code)])

    assert len(findings) == 1
    finding = findings[0]
    assert finding.check == "preprocess_before_split"
    assert finding.severity == "alta"
    assert finding.cell == 0
    assert finding.line == 4
    assert finding.snippet == "scaler.fit_transform(X)"
    assert "`X`" in finding.message


def test_fit_after_split_of_same_variable_is_ignored():
    code = "\n".join(
        [
            "from sklearn.preprocessing import StandardScaler",
            "from sklearn.model_selection import train_test_split",
            "train_test_split(X, y)",
            "scaler = StandardScaler()",
            "scaler.fit(X)",
        ]
    )

    assert check([_cell(0, code)]) == []


def test_fit_in_earlier_cell_is_reported_on_that_cell():
    fit_code = "\n".join(
        [
            "from sklearn.impute import SimpleImputer",
            "imputer = SimpleImputer()",
            "imputer.fit(X)",
        ]
    )
    split_code = "\n".join(
        [
            "from sklearn.model_selection import train_test_split",
            "train_test_split(X, y)",
        ]
    )

    findings = check([_cell(2, fit_code), _cell(4, split_code)])

    assert len(findings) == 1
    assert findings[0].cell == 2
    assert findings[0].line == 3
    assert findings[0].snippet == "imputer.fit(X)"
    assert findings[0].severity == "alta"


def test_split_of_transformed_variable_is_flagged():
    code = "\n".join(
        [
            "from sklearn.preprocessing import StandardScaler",
            "from sklearn.model_selection import train_test_split",
            "scaler = StandardScaler()",
            "X_scaled = scaler.fit_transform(X)",
            "train_test_split(X_scaled, y)",
        ]
    )

    findings = check([_cell(0, code)])

    assert len(findings) == 1
    assert findings[0].snippet == "X_scaled = scaler.fit_transform(X)"
    assert "`X_scaled`" in findings[0].message


def test_training_only_fit_is_ignored():
    cells = load_cells(FIXTURES / "script_split.py")

    assert check(cells) == []


def test_model_fit_before_split_is_ignored():
    code = "\n".join(
        [
            "from sklearn.linear_model import LogisticRegression",
            "from sklearn.model_selection import train_test_split",
            "LogisticRegression().fit(X, y)",
            "train_test_split(X, y)",
        ]
    )

    assert check([_cell(0, code)]) == []


def test_import_alias_is_recognized():
    code = "\n".join(
        [
            "from sklearn.preprocessing import MinMaxScaler as Scaler",
            "from sklearn.model_selection import train_test_split",
            "scaler = Scaler()",
            "scaler.fit(X)",
            "train_test_split(X, y)",
        ]
    )

    findings = check([_cell(0, code)])

    assert len(findings) == 1
    assert "MinMaxScaler.fit" in findings[0].message


def test_syntax_error_does_not_stop_the_check():
    broken = _cell(0, "def (\n")
    leak = _cell(
        3,
        "\n".join(
            [
                "from sklearn.decomposition import PCA",
                "PCA().fit_transform(X)",
                "from sklearn.model_selection import train_test_split",
                "train_test_split(X, y)",
            ]
        ),
    )

    findings = check([broken, leak])

    assert len(findings) == 1
    assert findings[0].cell == 3
    assert findings[0].snippet == "PCA().fit_transform(X)"
