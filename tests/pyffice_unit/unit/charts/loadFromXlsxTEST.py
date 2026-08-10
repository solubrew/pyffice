"""Tests for T-NEW-067 — PyfficeChart.load_from_xlsx (direct chart loading).

The user's testing-report_20260810.md line 24:
> "chart direct loading same to create worksheet if opened
> from worksheet with option to nextract chart and data only".

This card adds ``PyfficeChart.load_from_xlsx(file_path,
chart_index=0, include_data=True)`` for the case where the
user opens a ``.xlsx`` containing a chart directly — the
desktop should open a Chart tab (not a Matrix tab). When
``include_data=True`` (the default), the underlying worksheet
cells are also loaded into ``self.data`` so the chart tab can
show the data alongside the rendered chart.

This file pins 4 invariants the T-NEW-067 implementation
promises:

  1. ``test_load_from_xlsx_method_exists`` — the method is
     defined on ``PyfficeChart``.

  2. ``test_load_from_xlsx_returns_self`` — the method is
     chainable (returns ``self``) even when the file has no
     charts.

  3. ``test_load_from_xlsx_no_charts_is_noop`` — when the
     active worksheet has no charts, ``self.type`` stays
     ``None`` (no garbage from a partial load).

  4. ``test_load_from_xlsx_include_data_false_skips_cells`` —
     when ``include_data=False``, ``self.data`` stays ``None``.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJ_ROOT = Path("/home/solubrew/.hermes/projects/pyffice")
sys.path.insert(0, str(PROJ_ROOT))
sys.path.insert(0, str(PROJ_ROOT / "pyffice"))


def test_load_from_xlsx_method_exists():
    """``load_from_xlsx`` is defined on PyfficeChart."""
    from pyffice.charts.charts import PyfficeChart
    assert hasattr(PyfficeChart, "load_from_xlsx"), (
        "T-NEW-067 missing: PyfficeChart.load_from_xlsx"
    )


def test_load_from_xlsx_returns_self():
    """Method is chainable (returns self) even on no-op paths."""
    from pyffice.charts.charts import PyfficeChart
    chart = PyfficeChart()
    # Patch openpyxl so we don't need a real file.
    with patch("pyffice.charts.charts.openpyxl", create=True) as mock_openpyxl:
        # Configure the mock to raise so we hit the early-return
        # branch (no openpyxl installed → no-op + return self).
        mock_openpyxl.load_workbook.side_effect = ImportError("stub")
        result = chart.load_from_xlsx("/fake/path.xlsx")
    assert result is chart, (
        f"load_from_xlsx should return self for chainability; "
        f"got {type(result).__name__}"
    )


def test_load_from_xlsx_no_charts_is_noop():
    """When the active worksheet has no charts, type stays None."""
    from pyffice.charts.charts import PyfficeChart
    chart = PyfficeChart()
    # Mock openpyxl so the active worksheet has _charts=[].
    fake_ws = MagicMock()
    fake_ws._charts = []
    fake_ws.title = "Sheet1"
    fake_wb = MagicMock()
    fake_wb.active = fake_ws
    fake_openpyxl = MagicMock()
    fake_openpyxl.load_workbook.return_value = fake_wb
    with patch("pyffice.charts.charts.openpyxl", fake_openpyxl, create=True):
        result = chart.load_from_xlsx("/fake/no_charts.xlsx")
    assert result is chart
    # No type was loaded — type stays None (default).
    assert chart.config.dikt.get("type") is None, (
        f"chart.config.dikt['type'] should remain None for "
        f"no-charts load; got {chart.config.dikt.get('type')!r}"
    )


def test_load_from_xlsx_include_data_false_skips_cells():
    """``include_data=False`` leaves ``self.data`` as None."""
    from pyffice.charts.charts import PyfficeChart

    # Reuse the BarChart / _FakeAnchorTwoCell fakes from the
    # matrix chart-extraction tests — defined inline here to
    # avoid coupling between test files.
    class _FakeAnchorFrom:
        def __init__(self, col, row):
            self.col = col
            self.row = row
    class _FakeAnchorTwoCell:
        def __init__(self, from_col, from_row, to_col, to_row):
            self._from = _FakeAnchorFrom(from_col, from_row)
            self.to = _FakeAnchorFrom(to_col, to_row)
    class BarChart:
        def __init__(self, title="Sales"):
            self.title = None  # no title
            self.series = []
            self.anchor = _FakeAnchorTwoCell(0, 0, 5, 5)

    chart = PyfficeChart()
    chart.data = None  # ensure baseline

    # Build a fake worksheet that has iter_rows + _charts.
    fake_ws = MagicMock()
    fake_ws._charts = [BarChart()]
    fake_ws.title = "Data"
    # iter_rows should NOT be called when include_data=False;
    # make it raise so we'd notice if it were.
    fake_ws.iter_rows.side_effect = AssertionError(
        "iter_rows should NOT be called when include_data=False"
    )
    fake_wb = MagicMock()
    fake_wb.active = fake_ws
    # Inject a fake openpyxl module into sys.modules so the
    # ``import openpyxl`` inside load_from_xlsx resolves to
    # our mock. This is more reliable than ``create=True`` on
    # patch (which fails for module names that don't exist yet).
    fake_openpyxl = MagicMock()
    fake_openpyxl.load_workbook.return_value = fake_wb
    sys.modules["openpyxl"] = fake_openpyxl
    try:
        result = chart.load_from_xlsx(
            "/fake/chart_only.xlsx", include_data=False,
        )
    finally:
        del sys.modules["openpyxl"]
    assert result is chart
    # Type was loaded.
    assert chart.config.dikt.get("type") == "BarChart", (
        f"chart.config.dikt['type'] should be 'BarChart' after "
        f"load_from_xlsx; got {chart.config.dikt.get('type')!r}"
    )
    # Data was NOT loaded.
    assert chart.data is None, (
        f"chart.data should remain None when include_data=False; "
        f"got {chart.data!r}"
    )
