"""Testes do parser de scripts e notebooks."""

from pathlib import Path

import pytest

from revisor.parser import Call, load_cells

FIXTURES = Path(__file__).parent / "fixtures"


def test_script_becomes_one_cell_with_resolved_calls():
    cells = load_cells(FIXTURES / "script_split.py")

    assert len(cells) == 1
    cell = cells[0]
    assert cell.index == 0
    assert "train_test_split(X, y)" in cell.code
    assert cell.calls == [
        Call("sklearn.model_selection.train_test_split", 6),
        Call("sklearn.preprocessing.StandardScaler", 7),
        Call("scaler.fit_transform", 8),
    ]


def test_import_aliases_resolve_to_full_names():
    cells = load_cells(FIXTURES / "import_aliases.py")

    assert cells[0].calls == [
        Call("numpy.random.seed", 5),
        Call("sklearn.model_selection.train_test_split", 6),
        Call("sklearn.model_selection.train_test_split", 7),
    ]


def test_notebook_skips_markdown_and_keeps_original_index():
    cells = load_cells(FIXTURES / "notebook_cells.ipynb")

    assert [cell.index for cell in cells] == [1, 3]
    assert all("markdown" not in cell.code for cell in cells)
    assert cells[0].calls == [
        Call("sklearn.model_selection.train_test_split", 2),
    ]
    assert cells[1].calls == []
    assert cells[1].code.startswith("def (")


def test_syntax_error_returns_cell_without_calls():
    cells = load_cells(FIXTURES / "syntax_error.py")

    assert len(cells) == 1
    assert cells[0].index == 0
    assert cells[0].code.startswith("def (")
    assert cells[0].calls == []


def test_unsupported_extension_raises():
    with pytest.raises(ValueError, match="formato não suportado"):
        load_cells(FIXTURES / "script_split.py.txt")
