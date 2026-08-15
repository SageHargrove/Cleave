"""Entra ID (Azure AD) flavoured export (group-membership centric, GUID groups).

Quirks exercised (FR-ING-11): GUID group identifiers, and a users file written
in a non-UTF-8 encoding (Windows-1252).
"""

from __future__ import annotations

from pathlib import Path

from ..assignments import direct_grants
from ..model import Company
from ..rng import derive_guid
from .base import Dialect, StreamingCsvWriter


class EntraDialect(Dialect):
    name = "entra"

    def emit(self, company: Company, out_dir: str | Path) -> list[Path]:
        out = Path(out_dir) / "entra"
        paths: list[Path] = []

        # Users — deliberately written as Windows-1252 (non-UTF-8) to exercise
        # encoding detection in the importer.
        with StreamingCsvWriter(
            out / "entra_users.csv",
            [
                "userPrincipalName",
                "displayName",
                "accountEnabled",
                "department",
                "jobTitle",
                "objectId",
            ],
            encoding="cp1252",
        ) as w:
            for ident in company.identities:
                w.write(
                    [
                        ident.email,
                        ident.display_name,
                        "true" if ident.status == "active" else "false",
                        ident.department,
                        ident.title,
                        derive_guid(company.seed, "user", ident.id),
                    ]
                )
            paths.append(w.path)

        # Groups (only group-kind entitlements; identified by GUID objectId).
        with StreamingCsvWriter(
            out / "entra_groups.csv",
            ["objectId", "displayName", "securityEnabled"],
        ) as w:
            for ent in company.entitlements:
                if not ent.is_group:
                    continue
                w.write(
                    [
                        derive_guid(company.seed, "group", ent.id),
                        ent.name,
                        "true",
                    ]
                )
            paths.append(w.path)

        # Group memberships (one row per (user, group); streamed per identity).
        with StreamingCsvWriter(
            out / "entra_group_members.csv",
            ["groupObjectId", "memberUserPrincipalName"],
        ) as w:
            for ident in company.identities:
                for eid in sorted(direct_grants(company, ident)):
                    ent = company.entitlement(eid)
                    if not ent.is_group:
                        continue
                    w.write(
                        [
                            derive_guid(company.seed, "group", ent.id),
                            ident.email,
                        ]
                    )
            paths.append(w.path)

        return paths
