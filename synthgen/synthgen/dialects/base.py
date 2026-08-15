"""Dialect interface and shared streaming writers (task 7.1).

The writers emit rows one at a time and never accumulate the full table, so the
5M-assignment tier streams within memory budget (design D5). Both a CSV and a
minimal XLSX writer are provided; dialects choose per file.
"""

from __future__ import annotations

import csv
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from pathlib import Path

from ..model import Company

MULTIVALUE_SEP = ";"  # convention for packing many values into one cell


class StreamingCsvWriter:
    """A CSV writer supporting delimiter/encoding variety and messy quirks.

    ``preamble`` rows are written *before* the header (producing a header that
    is not on row 1); ``trailing`` rows can be appended to mimic total rows.
    """

    def __init__(
        self,
        path: str | Path,
        header: Sequence[str],
        *,
        delimiter: str = ",",
        encoding: str = "utf-8",
        preamble: Iterable[Sequence[object]] = (),
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", newline="", encoding=encoding, errors="replace")
        self._w = csv.writer(self._fh, delimiter=delimiter)
        for row in preamble:
            self._w.writerow(list(row))
        self._w.writerow(list(header))
        self.rows_written = 0

    def write(self, row: Sequence[object]) -> None:
        self._w.writerow(list(row))
        self.rows_written += 1

    def write_trailing(self, rows: Iterable[Sequence[object]]) -> None:
        for row in rows:
            self._w.writerow(list(row))

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> StreamingCsvWriter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _xml_escape(value: object) -> str:
    s = str(value)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class StreamingXlsxWriter:
    """A minimal, valid, streaming XLSX writer (single sheet, inline strings).

    Static parts are written up front; sheet rows stream into the zip entry so
    no full-table buffer is required.
    """

    _CONTENT_TYPES = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    _RELS = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    _WORKBOOK = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    _WB_RELS = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )

    def __init__(self, path: str | Path, header: Sequence[str]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._zip = zipfile.ZipFile(self.path, "w", zipfile.ZIP_DEFLATED)
        self._zip.writestr("[Content_Types].xml", self._CONTENT_TYPES)
        self._zip.writestr("_rels/.rels", self._RELS)
        self._zip.writestr("xl/workbook.xml", self._WORKBOOK)
        self._zip.writestr("xl/_rels/workbook.xml.rels", self._WB_RELS)
        self._sheet = self._zip.open("xl/worksheets/sheet1.xml", "w")
        self._write_raw(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
        )
        self.rows_written = 0
        self.write(header)

    def _write_raw(self, text: str) -> None:
        self._sheet.write(text.encode("utf-8"))

    def write(self, row: Sequence[object]) -> None:
        cells = "".join(
            f'<c t="inlineStr"><is><t xml:space="preserve">{_xml_escape(v)}</t></is></c>'
            for v in row
        )
        self._write_raw(f"<row>{cells}</row>")
        self.rows_written += 1

    def close(self) -> None:
        self._write_raw("</sheetData></worksheet>")
        self._sheet.close()
        self._zip.close()

    def __enter__(self) -> StreamingXlsxWriter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class Dialect(ABC):
    """One vendor's view of a company."""

    name: str = "base"

    @abstractmethod
    def emit(self, company: Company, out_dir: str | Path) -> list[Path]:
        """Write this dialect's files under ``out_dir``; return the paths."""
        raise NotImplementedError
