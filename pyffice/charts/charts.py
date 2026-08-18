# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@||
"""
---
<(META)>:
    docid:
    name:
    description: >
    version: 0.0.0.0.0.0
    authority: filesystem
    security: seclvl2
    <(WT)>: -32
"""

from copy import deepcopy

# -*- coding: utf-8 -*
# ======================================Standard Library Modules======================================================||
from os.path import abspath, dirname, join
import datetime as dt

# ======================================3rd Party Library Modules=====================================================||

# ======================================Solutions Brewer Library Modules==============================================||
from kahndor import kahndor
from kahndor.logma import Logma
from pyffice.ports.msports import PyfficePortExcel
from pyffice.document import PyfficeDocument, PyfficeDocumentManager
from pyffice.items.text import PyfficeText
from pyffice.analytics.sources import PyfficeDataSet
from typing import Any
from typing_extensions import Self

# ====================================================================================================================||
here = join(dirname(__file__), "")  # ||
log = True
logma = Logma(__name__)

# ====================================================================================================================||
pxcfg = join(here, "_data_", "charts.yaml")


class PyfficeChart(PyfficeDocument):
    SERIALIZATION_VERSION = (0, 0, 1, 0, 1, 2)
    """
    A flexible general-purpose charting class for creating various charts using Seaborn and Matplotlib.
    """

    def __init__(self, cfg=None) -> None:
        """
        Initialize the chart with default configurations.

        Args:
            title (str): Title of the chart.
            xlabel (str): Label for the X-axis.
            ylabel (str): Label for the Y-axis.
            figsize (tuple): Size of the figure (width, height).
        """
        super().__init__(cfg)
        self.config.override(kahndor.Instruct(pxcfg).select("PyfficeChart")).override(cfg)
        self.axes = None
        self.background = None
        self.compatibility = None
        self.data = None  # Store the chart's data
        self.figsize = None
        self.legends = None
        self.origin = None
        self.orientation = None
        self.plotareas = None
        self.position = None
        self.porter = None
        self.series = None  # Stores individual series configurations
        self.size = None
        self.theme = None
        self.title = None
        self.type = None
        self.xlabel = None
        self.ylabel = None

    def _merge_config(self, user_data, config_key, fields) -> Any:
        """Merge user-supplied dict with defaults from config.

        Args:
            user_data: User-supplied dict (may be None).
            config_key: Key in self.config.dikt for defaults.
            fields: List of field names to merge.

        Returns:
            Merged dict.
        """
        defaults = self.config.dikt.get(config_key, {})
        user_data = user_data or {}
        return {f: user_data.get(f, defaults.get(f)) for f in fields}

    def add_axis(self, axis) -> Self:
        """Add a axis.

        Args:
            axis: Parameter.

        Returns:
            Self for chaining.
        """
        axis = self._merge_config(
            axis,
            "axis",
            [
                "dimension",
                "title",
                "label",
                "position",
                "size",
                "orientation",
                "start",
                "step",
                "labels",
                "primary",
            ],
        )
        self.axes.append(axis)
        return self

    def add_legend(self, legend) -> Self:
        """Add a legend.

        Args:
            legend: Parameter.

        Returns:
            Self for chaining.
        """
        default_legend = self.config.dikt.get("legend", {})
        legend = {
            "position": legend.get("position", default_legend.get("position", None)),
            "size": legend.get("size", default_legend.get("size", None)),
            "color": legend.get("color", default_legend.get("color", None)),
            "image": legend.get("image", default_legend.get("image", None)),
            "border": legend.get("border", default_legend.get("border", None)),
            "translucence": legend.get("translucence", default_legend.get("translucence", None)),
        }
        self.legends.append(legend)
        return self

    def add_plotarea(self, plotarea) -> Self:
        """Add a plotarea.

        Args:
            plotarea: Parameter.

        Returns:
            Self for chaining.
        """
        default_plotarea = self.config.dikt.get("plotarea", {})
        plotarea = {
            "position": plotarea.get("position", default_plotarea.get("position", None)),
            "size": plotarea.get("size", default_plotarea.get("size", None)),
            "background": plotarea.get("background", default_plotarea.get("background", None)),
            "axes": plotarea.get("axes", default_plotarea.get("axes", None)),
            "translucence": plotarea.get("translucence", default_plotarea.get("translucence", None)),
            "color": plotarea.get("color", default_plotarea.get("color", None)),
        }
        self.plotareas.append(plotarea)
        return self

    def add_series(self, label, x_index: list, y_index: list, z_index=None, format_=None) -> Self:
        """
        Add a new series to the chart.

        Args:
            x (list): Data for the X-axis.
            y (list): Data for the Y-axis.
            label (str): Label for the legend.
            **kwargs: Additional keyword arguments for Seaborn or Matplotlib plots (e.g., color, linestyle).
        """
        format_ = self._merge_config(
            format_,
            "series",
            [
                "marker",
                "markersize",
                "linestyle",
                "linewidth",
                "pattern",
                "fill",
                "fill_color",
                "marker_color",
                "line_color",
                "show_labels",
            ],
        )
        defaults = {
            "marker": "circle",
            "markersize": 10,
            "linestyle": "solid",
            "linewidth": 1,
            "fill": True,
            "fill_color": "blue",
            "marker_color": "blue",
            "line_color": "blue",
            "show_labels": True,
        }
        for key, val in defaults.items():
            if format_.get(key) is None:
                format_[key] = val
        self.series[label] = {"x": x_index, "y": y_index, "z": z_index, "format": format_}
        return self

    def del_axis(self, axis) -> Self:
        """Remove the axis.

        Args:
            axis: Parameter.

        Returns:
            Self for chaining.
        """
        self.add_change("axes", deepcopy(self.axes), axis)
        del self.axes[axis]
        return self

    def del_legend(self, legend) -> Self:
        """Remove the legend.

        Args:
            legend: Parameter.

        Returns:
            Self for chaining.
        """
        self.add_change("legends", deepcopy(self.legends), legend)
        del self.legends[legend]
        return self

    def del_plotarea(self, plotarea) -> Self:
        """Remove the plotarea.

        Args:
            plotarea: Parameter.

        Returns:
            Self for chaining.
        """
        self.add_change("plotareas", deepcopy(self.plotareas), plotarea)
        del self.plotareas[plotarea]
        return self

    def del_series(self, series) -> Self:
        """Remove the series.

        Args:
            series: Parameter.

        Returns:
            Self for chaining.
        """
        self.add_change("series", deepcopy(self.series), series)
        del self.series[series]
        return self

    def load_document(self, document=None) -> Self:
        """Load document into this document.

        Args:
            document: Parameter.

        Returns:
            Self for chaining.
        """
        logma.info(f"Load Document {document}")
        if document is None:
            document = self.config.dikt.get("document", {})
            if document is None:
                document = {}
        super().load_document(document)
        self.set_chart_type(document.get("type", None))
        self.set_data(document.get("data", None))  # Store the chart's data
        self.set_figsize(document.get("figsize", (10, 6)))  # Default figure size
        self.set_label_xaxis(document.get("xlabel", None))
        self.set_label_yaxis(document.get("ylabel", None))
        self.set_legends(document.get("legends", []))
        self.set_origin(document.get("origin", []))
        self.set_plotareas(document.get("plotareas", []))
        self.set_position(document.get("position", None))
        self.set_series(document.get("series", []))
        self.set_theme(document.get("theme", None))
        self.set_title(document.get("title", None))
        return self

    def save(self, path=None, syntax=None, encrypt_key=None) -> Self:
        """Save the document.

        Args:
            path: Parameter.
            syntax: Parameter.
            encrypt_key: Parameter.

        Returns:
            Self for chaining.
        """
        if syntax is None:
            syntax = self.compatibility
        super().save(path, syntax, encrypt_key)
        if path is None:
            return self
        match syntax:
            case "latex":
                self.save_latex(path)
            case "excel":
                self.save_excel(path)
            case "html":
                self.save_html(path)
            case _:
                self.save_pyffice(path, syntax, encrypt_key)
        return self

    def save_excel(self, path) -> None:
        """Save the document.

        Args:
            path: Parameter.

        Returns:
            Self for chaining.
        """
        porter = PyfficePortExcel({"parent": self})
        porter.file_export(self, path)

    def load_from_xlsx(
        self,
        file_path,
        chart_index=0,
        include_data=True,
    ) -> Self:
        """T-NEW-067: load a chart directly from an ``.xlsx`` file.

        Companion to ``PyfficeMatrix.load_excel`` (which extracts
        charts as a side-effect of loading a worksheet). This
        method is for the case where the user wants to open
        a chart directly — e.g. double-click a ``.xlsx`` file
        that contains a chart and the desktop should open a
        Chart tab, not a Matrix tab.

        Args:
            file_path: Path to the ``.xlsx`` file.
            chart_index: Which chart to load (default 0 — the
                first chart in the active worksheet). Use a
                higher index to load the N-th chart.
            include_data: When True (default), also load the
                underlying worksheet cells into
                ``self.data``. The user-reported
                "option to extract chart and data only"
                requirement (testing-report_20260810.md
                line 24) is satisfied by this default; pass
                ``include_data=False`` for chart-only loading.

        Returns:
            Self for chaining.
        """
        try:
            import openpyxl
        except ImportError:
            logma.warning(f"[PyfficeChart] load_from_xlsx: openpyxl not " f"installed; cannot load {file_path}.")
            return self
        try:
            wb = openpyxl.load_workbook(
                file_path,
                data_only=False,
            )
            ws = wb.active
            openpyxl_charts = getattr(ws, "_charts", []) or []
            if not openpyxl_charts:
                logma.info(f"[PyfficeChart] load_from_xlsx: {file_path} " f"has no charts in active sheet; no-op.")
                return self
            if chart_index >= len(openpyxl_charts):
                logma.warning(
                    f"[PyfficeChart] load_from_xlsx: chart_index="
                    f"{chart_index} out of range (file has "
                    f"{len(openpyxl_charts)} charts); defaulting "
                    f"to chart 0."
                )
                chart_index = 0
            oc = openpyxl_charts[chart_index]
            # Use the same metadata-extraction pattern as
            # PyfficeMatrix._chart_from_openpyxl (T-NEW-066).
            # Inlined here to avoid a cross-module import
            # cycle (matrix imports from charts).
            chart_type = type(oc).__name__
            title = None
            try:
                title_obj = getattr(oc, "title", None)
                if title_obj is not None and getattr(title_obj, "tx", None) is not None:
                    tx = title_obj.tx
                    if getattr(tx, "rich", None) is not None and tx.rich.p:
                        runs = tx.rich.p[0].r
                        if runs and hasattr(runs[0], "t"):
                            title = runs[0].t
                    if title is None and getattr(tx, "strRef", None) is not None:
                        title = str(tx.strRef.f)
            except Exception:
                pass
            position = None
            try:
                anchor = getattr(oc, "anchor", None)
                if anchor is not None:
                    _from = getattr(anchor, "_from", None)
                    if _from is not None:
                        position = {
                            "from_col": getattr(_from, "col", None),
                            "from_row": getattr(_from, "row", None),
                        }
                        _to = getattr(anchor, "to", None)
                        if _to is not None:
                            position["to_col"] = getattr(_to, "col", None)
                            position["to_row"] = getattr(_to, "row", None)
            except Exception:
                pass
            series_count = 0
            first_series_title = None
            try:
                series_list = getattr(oc, "series", []) or []
                series_count = len(series_list)
                if series_count > 0:
                    s0 = series_list[0]
                    if getattr(s0, "tx", None) is not None and getattr(s0.tx, "strRef", None) is not None:
                        first_series_title = str(s0.tx.strRef.f)
            except Exception:
                pass
            cfg = {
                "type": chart_type,
                "title": title,
                "position": position,
                "openpyxl_index": chart_index,
                "series_count": series_count,
                "first_series_title": first_series_title,
                "source_file": file_path,
                "source_sheet": ws.title,
            }
            # Delegate to load_document (existing pattern at
            # line 226) — it reads ``type``, ``data``,
            # ``figsize``, axes, legends, etc. from cfg.
            self.load_document(cfg)
            if include_data:
                # Load the underlying worksheet cells into
                # ``self.data`` so the chart tab can show the
                # data alongside the rendered chart.
                try:
                    rows = []
                    for row in ws.iter_rows(values_only=True):
                        rows.append([str(c) if c is not None else "" for c in row])
                    self.data = rows
                except Exception as de:
                    logma.warning(f"[PyfficeChart] load_from_xlsx: data " f"load failed for {file_path}: {de}")
            logma.info(
                f"[PyfficeChart] load_from_xlsx: loaded chart "
                f"#{chart_index} (type={chart_type!r}, "
                f"title={title!r}) from {file_path}; "
                f"include_data={include_data}, "
                f"data_rows={len(self.data) if include_data else 0}."
            )
        except (OSError, KeyError, ValueError) as e:
            logma.warning(
                f"[PyfficeChart] load_from_xlsx: failed for " f"{file_path}: {e}",
                exc_info=True,
            )
        return self

    def save_html(self, path) -> Self:
        """Save chart as HTML file."""
        import os

        # Placeholder - would use plotting library to generate HTML
        return self

    def save_latex(self, path) -> Self:
        """Save chart as LaTeX file."""
        if not path:
            return self
        # Placeholder - would use plotting library to generate LaTeX
        return self

    def set_axes(self, axes) -> Self:
        """Set chart axes."""
        self.axes = axes
        return self

    def set_background(self, color=None) -> Self:
        """Set chart background."""
        self.background = color or "white"
        return self

    def set_chart_type(self, chart_type) -> Self:
        """Set the chart type.

        Args:
            chart_type: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("type", chart_type)

    def set_compatibility(self, compatibility) -> Self:
        """Set the compatibility.

        Args:
            compatibility: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("compatibility", compatibility)

    def set_data(self, data) -> Self:
        """Set chart data."""
        self.data = data
        return self

    def set_figsize(self, figsize) -> Self:
        """Set the figsize.

        Args:
            figsize: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("figsize", figsize)

    def set_label_xaxis(self, label) -> Self:
        """Set the label xaxis.

        Args:
            label: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("xlabel", label)

    def set_label_yaxis(self, label) -> Self:
        """Set the label yaxis.

        Args:
            label: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("ylabel", label)

    def set_legends(self, legends: list = None) -> Self:
        """Set the legends.

        Args:
            legends: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("legends", legends)

    def set_orientation(self, orientation) -> Self:
        """Set the orientation.

        Args:
            orientation: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("orientation", orientation)

    def set_origin(self, origin: list = None) -> Self:
        """Set the origin.

        Args:
            origin: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("origin", origin)

    def set_plotareas(self, plotareas) -> Self:
        """Set the plotareas.

        Args:
            plotareas: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("plotareas", plotareas)

    def set_position(self, position) -> Self:
        """Set the position.

        Args:
            position: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("position", position)

    def set_position_plotarea(self, position, plotarea=None) -> Self:
        """Set plot area position."""
        self.plotarea_position = position
        return self

    def set_position_legend(self, position, legend=None) -> Self:
        """Set legend position."""
        self.legend_position = position
        return self

    def set_series(self, series: list = None) -> Self:
        """Set the series.

        Args:
            series: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("series", series)

    def set_size(self, size) -> Self:
        """Set the size.

        Args:
            size: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("size", size)

    def set_size_plotarea(self, size, plotarea) -> Self:
        """Set plot area size."""
        self.plotarea_size = size
        return self

    def set_size_legend(self, size, legend) -> Self:
        """Set legend size."""
        self.legend_size = size
        return self

    def set_theme(self, theme="whitegrid") -> Self:
        """Set the theme.

        Args:
            theme: Parameter.

        Returns:
            Self for chaining.
        """
        return self._set_with_change("theme", theme, label="style")

    def set_title(self, title, size: int = 12, color: str = "black") -> Self:
        """Set the title.

        Args:
            title: Parameter.
            size: Parameter.
            color: Parameter.

        Returns:
            Self for chaining.
        """
        cfg = {
            "value": title,
            "alignment": {"horizontal": "center", "vertical": "center", "wrap": True},
            "font": {"color": color, "style": "sans-serif", "size": size, "bold": True},
        }
        title = PyfficeText(cfg)
        if title != self.title:
            self.add_change("title", self.title, title)
            self.title = title
        return self


# ====================================================================================================================||

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@||
