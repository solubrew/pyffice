"""T-NEW-159: PDF binary-blob round-trip through PyfficePDF.

PyfficePDF previously returned an empty bytes object from
``get_binary()``. The internal storage contract requires real
bytes that round-trip back through ``set_content`` on a fresh
document.
"""

from pathlib import Path

import pytest

from pyffice.pyffice import PyfficePDF, UnknownLocationError


PYTEST_HEADER_TEXT = (
    "T-NEW-159 -- PDF binary storage round-trip through get_binary/set_content"
)


SAMPLE_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
)


def test_pyfficePDF_get_binary_returns_empty_bytes_for_blank_document():
    """Default state: an unsaved PDF has no bytes yet."""
    pdf = PyfficePDF({})
    assert pdf.get_binary() == b""


def test_pyfficePDF_set_content_internal_loads_binary_from_file(tmp_path: Path):
    """Internal content reads the PDF bytes from disk and exposes them."""
    src = tmp_path / "src.pdf"
    src.write_bytes(SAMPLE_PDF)
    pdf = PyfficePDF({})
    pdf.set_file_path(str(src))
    pdf.set_location("internal")
    pdf.set_content({"file_path": str(src)})
    assert pdf.location == "internal"
    content = pdf.content or {}
    assert content.get("bytes") == SAMPLE_PDF
    assert pdf.get_binary() == SAMPLE_PDF


def test_pyfficePDF_set_content_external_keeps_file_path_only(tmp_path: Path):
    """External content stores only the file path; bytes come from disk on read."""
    src = tmp_path / "external.pdf"
    src.write_bytes(SAMPLE_PDF)
    pdf = PyfficePDF({})
    pdf.set_file_path(str(src))
    pdf.set_location("external")
    pdf.set_content({"file_path": str(src)})
    assert pdf.location == "external"
    assert pdf.content == {"file_path": str(src)}


def test_pyfficePDF_set_content_unknown_location_raises():
    pdf = PyfficePDF({})
    pdf.set_location("cloud")
    with pytest.raises(UnknownLocationError):
        pdf.set_content({"file_path": "/tmp/file.pdf"})


def test_pyfficePDF_internal_round_trips_through_set_content(tmp_path: Path):
    """A fresh document reads the same bytes via get_binary after set_content."""
    src = tmp_path / "round.pdf"
    src.write_bytes(SAMPLE_PDF)
    pdf = PyfficePDF({})
    pdf.set_file_path(str(src))
    pdf.set_location("internal")
    pdf.set_content({"file_path": str(src)})
    captured = pdf.get_binary()

    reopened = PyfficePDF({})
    reopened.set_location("internal")
    reopened.set_content({"file_path": str(src), "bytes": captured})

    assert captured == SAMPLE_PDF
    assert reopened.location == "internal"
    assert reopened.get_binary() == captured
