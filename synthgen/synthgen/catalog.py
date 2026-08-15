"""Application + entitlement catalog with nested groups (tasks 3.1–3.3).

Naming is deliberately ugly and heterogeneous (``FIN_AP_APPR_L2``, GUID group
names, ``CN=...`` DNs, mixed case) to feed the messy-file parser (FR-ING-11).

Groups nest to a bounded depth without cycles: entitlements are created in
layers, and a group at layer *L* may only contain items from layers ``< L``.
This makes the membership graph a DAG whose longest chain is ``max_nesting_depth``.
"""

from __future__ import annotations

from .config import GenConfig
from .model import Application, Entitlement
from .rng import Rng, derive_guid, derive_id

_APP_CODES = [
    ("FIN", "Finance Cloud", "sailpoint"),
    ("HRIS", "Workday HR", "generic"),
    ("SAP", "SAP ERP", "sailpoint"),
    ("AD", "Active Directory", "ad"),
    ("AAD", "Entra ID", "entra"),
    ("SFDC", "Salesforce", "okta"),
    ("JIRA", "Jira", "generic"),
    ("GH", "GitHub Enterprise", "generic"),
    ("O365", "Microsoft 365", "entra"),
    ("NETW", "Network Shares", "ad"),
    ("BILL", "Billing Portal", "generic"),
    ("CRM", "CRM Suite", "okta"),
    ("DWH", "Data Warehouse", "generic"),
    ("VPN", "VPN Gateway", "ad"),
    ("PROC", "Procurement", "sailpoint"),
    ("LEGL", "Legal Vault", "generic"),
    ("MKTG", "Marketing Hub", "okta"),
    ("SUPP", "Support Desk", "generic"),
    ("SEC", "Security Console", "sailpoint"),
    ("BI", "Analytics BI", "generic"),
]
_MODULES = ["AP", "AR", "GL", "HR", "IT", "RPT", "ADM", "PAY", "PO", "INV"]
_ACTIONS = ["APPR", "VIEW", "EDIT", "ADMIN", "POST", "READ", "WRITE", "DELETE"]
_LEVELS = ["L1", "L2", "L3"]


def _permission_name(code: str, r: Rng) -> str:
    mod = r.choice(_MODULES)
    act = r.choice(_ACTIONS)
    lvl = r.choice(_LEVELS)
    return f"{code}_{mod}_{act}_{lvl}"


def _group_name(code: str, index: int, style: str, cfg: GenConfig, r: Rng) -> str:
    """A group name in one of several vendor-flavoured styles."""
    if style == "guid":
        return derive_guid(cfg.seed, "group", code, index)
    if style == "dn":
        mod = r.choice(_MODULES)
        return f"CN={code}-{mod}-Team,OU=Groups,DC=corp,DC=example,DC=com"
    if style == "role":
        return f"ROLE_{code}_{r.choice(_MODULES)}_{r.choice(_LEVELS)}"
    # readable/mixed-case
    return f"{code.title()} {r.choice(_MODULES)} Group {index}"


def generate_catalog(
    cfg: GenConfig, rng: Rng
) -> tuple[list[Application], list[Entitlement]]:
    """Generate 10–40 applications each with a nested entitlement catalog."""
    cat_rng = rng.child("catalog")
    n_apps = max(10, min(40, cfg.n_applications))

    # Choose app codes (cycle with a numeric suffix if we need > pool size).
    apps_meta: list[tuple[str, str, str]] = []
    for a in range(n_apps):
        base = _APP_CODES[a % len(_APP_CODES)]
        if a < len(_APP_CODES):
            apps_meta.append(base)
        else:
            code, name, vendor = base
            apps_meta.append((f"{code}{a}", f"{name} {a}", vendor))

    # Split the entitlement budget across apps (roughly even, min 3 each).
    per_app = max(3, cfg.n_entitlements // n_apps)

    applications: list[Application] = []
    entitlements: list[Entitlement] = []
    ent_index = 0

    for a, (code, app_name, vendor) in enumerate(apps_meta):
        app_id = derive_id("app", a, width=3)
        r = cat_rng.child(a)
        n_ent = per_app + r.randint(-2, 2)
        n_ent = max(3, n_ent)

        n_groups = int(round(n_ent * cfg.group_fraction))
        n_perms = n_ent - n_groups

        app_ent_ids: list[str] = []

        # Layer 0: leaf permissions.
        layers: list[list[str]] = [[]]
        seen_perm_names: set[str] = set()
        for _ in range(max(1, n_perms)):
            # ensure unique names within the app
            for _try in range(8):
                pname = _permission_name(code, r)
                if pname not in seen_perm_names:
                    break
            seen_perm_names.add(pname)
            eid = derive_id("ent", ent_index)
            ent_index += 1
            entitlements.append(
                Entitlement(id=eid, app_id=app_id, name=pname, kind="permission")
            )
            layers[0].append(eid)
            app_ent_ids.append(eid)

        # Layers 1..max_depth: groups that contain items from shallower layers.
        remaining_groups = n_groups
        depth = 1
        while remaining_groups > 0 and depth <= cfg.max_nesting_depth:
            # front-load lower layers so deep chains are rarer than shallow ones
            take = max(1, remaining_groups // (cfg.max_nesting_depth - depth + 1))
            take = min(take, remaining_groups)
            layer_ids: list[str] = []
            candidate_pool = [e for lyr in layers[:depth] for e in lyr]
            for _ in range(take):
                style = (
                    "guid"
                    if r.chance(cfg.guid_group_fraction)
                    else r.choice(["dn", "role", "readable"])
                )
                gname = _group_name(code, ent_index, style, cfg, r)
                # 2–5 children, at least one from the immediately-shallower layer
                # so genuine group→group nesting occurs.
                k = min(len(candidate_pool), r.randint(2, 5))
                children = r.sample(candidate_pool, k) if candidate_pool else []
                if depth >= 2 and layers[depth - 1]:
                    child_group = r.choice(layers[depth - 1])
                    if child_group not in children:
                        children = list(children) + [child_group]
                child_depth = max(
                    (entitlements[_find(entitlements, c)].depth for c in children),
                    default=0,
                )
                eid = derive_id("ent", ent_index)
                ent_index += 1
                entitlements.append(
                    Entitlement(
                        id=eid,
                        app_id=app_id,
                        name=gname,
                        kind="group",
                        contains=tuple(children),
                        depth=child_depth + 1,
                    )
                )
                layer_ids.append(eid)
                app_ent_ids.append(eid)
            layers.append(layer_ids)
            remaining_groups -= take
            depth += 1

        applications.append(
            Application(
                id=app_id,
                name=app_name,
                short_code=code,
                vendor_hint=vendor,
                entitlement_ids=tuple(app_ent_ids),
            )
        )

    return applications, entitlements


def _find(entitlements: list[Entitlement], eid: str) -> int:
    # entitlements are appended in id order (ent_000000, ...); parse the index.
    return int(eid.split("_")[1])
