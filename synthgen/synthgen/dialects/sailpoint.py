"""SailPoint-flavoured export (identity-centric, multi-value entitlement cells).

Quirk exercised (FR-ING-11): entitlements packed into a single ``;``-joined
multi-value cell per identity.
"""

from __future__ import annotations

from pathlib import Path

from ..assignments import direct_grants
from ..model import Company
from .base import MULTIVALUE_SEP, Dialect, StreamingCsvWriter


class SailPointDialect(Dialect):
    name = "sailpoint"

    def emit(self, company: Company, out_dir: str | Path) -> list[Path]:
        out = Path(out_dir) / "sailpoint"
        paths: list[Path] = []

        # Identities.
        with StreamingCsvWriter(
            out / "sailpoint_identities.csv",
            [
                "identityName",
                "email",
                "department",
                "title",
                "location",
                "managerName",
                "cloudLifecycleState",
            ],
        ) as w:
            for ident in company.identities:
                mgr = (
                    company.identity(ident.manager_id).display_name
                    if ident.manager_id
                    else ""
                )
                state = "active" if ident.status == "active" else "inactive"
                w.write(
                    [
                        ident.display_name,
                        ident.email,
                        ident.department,
                        ident.title,
                        ident.location,
                        mgr,
                        state,
                    ]
                )
            paths.append(w.path)

        # Entitlement catalog.
        with StreamingCsvWriter(
            out / "sailpoint_entitlements.csv",
            ["application", "value", "type"],
        ) as w:
            apps = {a.id: a.short_code for a in company.applications}
            for ent in company.entitlements:
                w.write(
                    [
                        apps.get(ent.app_id, ent.app_id),
                        ent.name,
                        "group" if ent.is_group else "entitlement",
                    ]
                )
            paths.append(w.path)

        # Access (streamed one identity at a time; multi-value entitlement cell).
        with StreamingCsvWriter(
            out / "sailpoint_access.csv",
            ["identityName", "email", "entitlements"],
        ) as w:
            for ident in company.identities:
                names = sorted(
                    company.entitlement(eid).name
                    for eid in direct_grants(company, ident)
                )
                w.write(
                    [
                        ident.display_name,
                        ident.email,
                        MULTIVALUE_SEP.join(names),
                    ]
                )
            paths.append(w.path)

        return paths
