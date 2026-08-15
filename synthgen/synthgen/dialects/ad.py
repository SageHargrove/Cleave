"""Active Directory flavoured export (tab-delimited, DN multi-values).

Quirks exercised (FR-ING-11): tab delimiter, a header that is not on row 1
(preamble comment lines), a trailing total row, and ``;``-joined
distinguished-name multi-value cells.
"""

from __future__ import annotations

from pathlib import Path

from ..assignments import direct_grants
from ..model import Company, Entitlement
from .base import MULTIVALUE_SEP, Dialect, StreamingCsvWriter


def _dn(ent: Entitlement) -> str:
    """Represent a group as an AD distinguished name."""
    if ent.name.startswith("CN="):
        return ent.name
    safe = ent.name.replace(",", " ")
    return f"CN={safe},OU=Groups,DC=corp,DC=example,DC=com"


class ADDialect(Dialect):
    name = "ad"

    def emit(self, company: Company, out_dir: str | Path) -> list[Path]:
        out = Path(out_dir) / "ad"
        paths: list[Path] = []
        preamble = [
            ["# Active Directory export"],
            [f"# domain: corp.example.com  seed-run: {company.seed}"],
            [],
        ]

        # Users — tab-delimited, header not on row 1, trailing total row.
        with StreamingCsvWriter(
            out / "ad_users.csv",
            [
                "sAMAccountName",
                "distinguishedName",
                "userAccountControl",
                "mail",
                "department",
            ],
            delimiter="\t",
            preamble=preamble,
        ) as w:
            for ident in company.identities:
                sam = f"{ident.first_name[0]}{ident.last_name}".lower()
                dn = (
                    f"CN={ident.display_name},OU={ident.department},"
                    "DC=corp,DC=example,DC=com"
                )
                # 512 = normal enabled, 514 = disabled
                uac = "512" if ident.status == "active" else "514"
                w.write([sam, dn, uac, ident.email, ident.department])
            w.write_trailing([["# TOTAL", len(company.identities)]])
            paths.append(w.path)

        # memberOf (streamed per identity; DN multi-value cell).
        with StreamingCsvWriter(
            out / "ad_memberof.csv",
            ["sAMAccountName", "memberOf"],
            delimiter="\t",
        ) as w:
            for ident in company.identities:
                sam = f"{ident.first_name[0]}{ident.last_name}".lower()
                dns = [
                    _dn(company.entitlement(eid))
                    for eid in sorted(direct_grants(company, ident))
                    if company.entitlement(eid).is_group
                ]
                if not dns:
                    continue
                w.write([sam, MULTIVALUE_SEP.join(dns)])
            paths.append(w.path)

        return paths
