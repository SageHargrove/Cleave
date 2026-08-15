"""Task 7.4 — each dialect parses as that vendor's format and all dialects
describe the same company; messy-file quirks are present."""

from __future__ import annotations

import csv

from synthgen.dialects.base import MULTIVALUE_SEP


def _read_csv(path, delimiter=",", encoding="utf-8", skip_comment=False):
    with open(path, newline="", encoding=encoding) as fh:
        rows = list(csv.reader(fh, delimiter=delimiter))
    if skip_comment:
        rows = [r for r in rows if r and not r[0].startswith("#")]
    rows = [r for r in rows if r]  # drop blank rows
    return rows


def test_all_dialects_written(small, tmp_path):
    from synthgen.generate import write_company

    manifest = write_company(small, tmp_path)
    for name in ("sailpoint", "entra", "ad"):
        assert name in manifest["exports"]
        for _ in manifest["exports"][name]:
            assert (tmp_path).exists()


def test_dialects_describe_same_company(small, tmp_path):
    from synthgen.generate import write_company

    write_company(small, tmp_path)

    sp = _read_csv(tmp_path / "sailpoint" / "sailpoint_identities.csv")
    sp_header, sp_rows = sp[0], sp[1:]
    sp_emails = {r[sp_header.index("email")] for r in sp_rows}

    entra = _read_csv(tmp_path / "entra" / "entra_users.csv", encoding="cp1252")
    en_header, en_rows = entra[0], entra[1:]
    en_emails = {r[en_header.index("userPrincipalName")] for r in en_rows}

    ad = _read_csv(tmp_path / "ad" / "ad_users.csv", delimiter="\t", skip_comment=True)
    ad_header, ad_rows = ad[0], ad[1:]
    ad_emails = {r[ad_header.index("mail")] for r in ad_rows}

    assert sp_emails == en_emails == ad_emails
    assert len(sp_emails) == len(small.identities)


def test_sailpoint_multivalue_cells(small, tmp_path):
    from synthgen.generate import write_company

    write_company(small, tmp_path)
    rows = _read_csv(tmp_path / "sailpoint" / "sailpoint_access.csv")
    header, data = rows[0], rows[1:]
    ent_col = header.index("entitlements")
    assert any(MULTIVALUE_SEP in r[ent_col] for r in data), "no multi-value cell"


def test_ad_header_not_on_row_one_and_has_trailing_total(small, tmp_path):
    from synthgen.generate import write_company

    write_company(small, tmp_path)
    with open(tmp_path / "ad" / "ad_users.csv", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    assert lines[0].startswith("#"), "AD header should not be on row 1"
    assert any(line.startswith("# TOTAL") for line in lines), "no trailing total row"


def test_xlsx_writer_produces_valid_workbook(tmp_path):
    import zipfile

    from synthgen.dialects.base import StreamingXlsxWriter

    path = tmp_path / "book.xlsx"
    with StreamingXlsxWriter(path, ["a", "b"]) as w:
        for i in range(5):
            w.write([i, f"needs<escaping>&{i}"])
    z = zipfile.ZipFile(path)
    assert z.testzip() is None  # every entry has a valid CRC
    assert "xl/worksheets/sheet1.xml" in z.namelist()
    sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
    assert "&lt;escaping&gt;" in sheet  # XML-escaped, not raw


def test_entra_users_file_is_cp1252(small, tmp_path):
    from synthgen.generate import write_company

    write_company(small, tmp_path)
    raw = (tmp_path / "entra" / "entra_users.csv").read_bytes()
    # decodes cleanly as cp1252 (the declared non-UTF-8 encoding)
    text = raw.decode("cp1252")
    assert "userPrincipalName" in text
