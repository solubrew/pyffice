"""Tests for T-NEW-066 — Matrix chart extraction from Excel workbooks.

The user's testing-report_20260810.md line 22:
> "NchantdMatrix needs debug with loading excel files
> including chart loading. chart direct loading same to
> create worksheet if opened from worksheet with option to
> nextract chart and data only".

This file pins 4 invariants the T-NEW-066 implementation
promises:

  1. ``test_extract_charts_helper_exists`` — the
     ``_extract_charts_from_worksheet`` method exists on
     ``PyfficeMatrix`` and returns a list.

  2. ``test_chart_from_openpyxl_class_mapping`` — when given
     a fake ``BarChart``-like object, the helper maps it
     to ``type="BarChart"`` and returns a ``PyfficeChart``.

  3. ``test_extract_charts_returns_empty_for_no_charts`` —
     when the worksheet has no ``_charts`` attribute (or it
     is an empty list), the helper returns ``[]``.

  4. ``test_extract_charts_graceful_for_missing_optional_attrs``
     — charts with ``title=None`` or ``anchor=None`` (common
     real-world cases in openpyxl) don't crash the helper;
     the affected chart is included with title=None /
     position=None in its cfg.

Uses plain Python classes (NOT MagicMock) for the fake
charts because ``type(oc).__name__`` is the contract — a
MagicMock would defeat the test by returning "MagicMock".
"""

import sys
from pathlib import Path

PROJ_ROOT = Path("/home/solubrew/.hermes/projects/pyffice")
sys.path.insert(0, str(PROJ_ROOT))
sys.path.insert(0, str(PROJ_ROOT / "pyffice"))


class _FakeRun:
    """Mimics openpyxl's ``rich.p[0].r[0].t`` text-run chain."""
    def __init__(self, text):
        self.t = text


class _FakeRichP:
    def __init__(self, text):
        self.r = [_FakeRun(text)]


class _FakeRich:
    def __init__(self, text):
        self.p = [_FakeRichP(text)]


class _FakeTx:
    def __init__(self, text):
        self.rich = _FakeRich(text)
        self.strRef = None


class _FakeTitle:
    def __init__(self, text):
        self.tx = _FakeTx(text)


class _FakeSeriesTx:
    def __init__(self, ref):
        self.strRef = type("_Ref", (), {"f": ref})()


class _FakeSeries:
    def __init__(self, title_ref):
        self.tx = _FakeSeriesTx(title_ref)


class _FakeAnchorFrom:
    def __init__(self, col, row):
        self.col = col
        self.row = row


class _FakeAnchorTwoCell:
    """Mimics openpyxl's TwoCellAnchor (has both _from and to)."""
    def __init__(self, from_col, from_row, to_col, to_row):
        self._from = _FakeAnchorFrom(from_col, from_row)
        self.to = _FakeAnchorFrom(to_col, to_row)


class BarChart:
    """Mimics openpyxl.chart.BarChart for the helper. Named exactly
    ``BarChart`` so ``type(oc).__name__`` returns the right string."""
    def __init__(self, title="Sales 2024"):
        self.title = _FakeTitle(title)
        self.series = [_FakeSeries("Sheet1!$B$2:$B$10")]
        self.anchor = _FakeAnchorTwoCell(1, 2, 5, 10)


class LineChart(BarChart):
    """Mimics openpyxl.chart.LineChart."""
    pass


class UntitledChart(BarChart):
    """Chart with ``title=None`` (a real-world case where
    openpyxl charts have no title set). Used to test that
    the helper doesn't crash when title is None — falls back
    gracefully to title=None."""

    def __init__(self):
        # Skip BarChart.__init__ to avoid setting a real title.
        self.title = None
        self.series = []
        self.anchor = _FakeAnchorTwoCell(0, 0, 5, 5)


class MissingAnchorChart(BarChart):
    """Chart with ``anchor=None`` (another real-world case).
    Used to test that the helper doesn't crash when the
    anchor is missing."""

    def __init__(self):
        self.title = _FakeTitle("NoAnchor")
        self.series = []
        self.anchor = None


def test_extract_charts_helper_exists():
    """``_extract_charts_from_worksheet`` exists on PyfficeMatrix."""
    from pyffice.matrix.matrix import PyfficeMatrix
    assert hasattr(PyfficeMatrix, "_extract_charts_from_worksheet"), (
        "T-NEW-066 missing: PyfficeMatrix._extract_charts_from_worksheet"
    )


def test_chart_from_openpyxl_class_mapping():
    """A fake ``BarChart`` is mapped to ``type="BarChart"`` + PyfficeChart."""
    from pyffice.charts.charts import PyfficeChart
    from pyffice.matrix.matrix import PyfficeMatrix

    m = PyfficeMatrix()
    oc = BarChart(title="Sales 2024")
    chart = m._chart_from_openpyxl(oc, index=0)
    assert chart is not None, (
        "_chart_from_openpyxl should not return None for a "
        "well-formed BarChart"
    )
    assert isinstance(chart, PyfficeChart), (
        f"expected PyfficeChart, got {type(chart).__name__}"
    )
    # The chart's cfg should carry the openpyxl metadata.
    assert chart.config.dikt.get("type") == "BarChart"
    assert chart.config.dikt.get("title") == "Sales 2024"
    assert chart.config.dikt.get("series_count") == 1
    assert chart.config.dikt.get("first_series_title") == "Sheet1!$B$2:$B$10"
    assert chart.config.dikt.get("openpyxl_index") == 0
    # Position (anchor) was captured.
    pos = chart.config.dikt.get("position")
    assert pos is not None
    assert pos["from_col"] == 1
    assert pos["from_row"] == 2
    assert pos["to_col"] == 5
    assert pos["to_row"] == 10


def test_chart_from_openpyxl_line_chart():
    """A fake ``LineChart`` is mapped to ``type="LineChart"``."""
    from pyffice.matrix.matrix import PyfficeMatrix

    m = PyfficeMatrix()
    oc = LineChart(title="Trend")
    chart = m._chart_from_openpyxl(oc, index=1)
    assert chart is not None
    assert chart.config.dikt.get("type") == "LineChart"
    assert chart.config.dikt.get("title") == "Trend"
    assert chart.config.dikt.get("openpyxl_index") == 1


def test_extract_charts_returns_empty_for_no_charts():
    """Worksheet without ``_charts`` returns ``[]``."""
    from pyffice.matrix.matrix import PyfficeMatrix

    m = PyfficeMatrix()

    class _WsNoCharts:
        _charts = []

    result = m._extract_charts_from_worksheet(_WsNoCharts())
    assert result == [], (
        f"Expected [] for empty _charts, got {result!r}"
    )


def test_extract_charts_graceful_for_missing_optional_attrs():
    """Charts with ``title=None`` or ``anchor=None`` don't crash."""
    from pyffice.matrix.matrix import PyfficeMatrix

    m = PyfficeMatrix()

    class _Ws:
        _charts = [UntitledChart(), MissingAnchorChart()]

    result = m._extract_charts_from_worksheet(_Ws())
    # Both charts survive — no exceptions escape.
    assert len(result) == 2, (
        f"Expected 2 charts (one with title=None, one with "
        f"anchor=None). Got {len(result)}: {result!r}"
    )
    # The title=None chart produces a PyfficeChart with
    # title=None (not the string "None").
    titles = [c.config.dikt.get("title") for c in result]
    assert None in titles, (
        f"Expected one chart with title=None; got titles={titles!r}"
    )
    # The anchor=None chart produces a PyfficeChart with
    # position=None (not a dict).
    positions = [c.config.dikt.get("position") for c in result]
    assert None in positions, (
        f"Expected one chart with position=None; got "
        f"positions={positions!r}"
    )
