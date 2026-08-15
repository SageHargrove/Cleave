"""Noise injection and planted, labeled findings (tasks 5.1–5.4, design D1).

Over-provisioning and legacy grants are computed on the fly per identity (see
:mod:`synthgen.assignments`); this module handles the parts that must be
*recorded* so algorithms can be scored against them:

* copy-paste-user artifacts (identities cloned from a template peer),
* planted outliers (a rare-for-peers entitlement, with the reason),
* planted SoD violations (toxic entitlement pairs, incl. via nested groups),

writing each into ``company.ground_truth`` and layering the exact extra grants
into ``ground_truth.extra_grants`` so the generator's invariants stay exact.
"""

from __future__ import annotations

from dataclasses import replace

from .config import GenConfig
from .model import Company, Identity, PlantedOutlier, PlantedSoD
from .rng import Rng, derive_id

_SOD_RULES = [
    "Create vendor / Approve payment",
    "Request access / Approve access",
    "Post journal / Approve journal",
    "Create PO / Approve PO",
    "Develop / Deploy to production",
    "Manage payroll / Approve payroll",
]


def inject_noise(company: Company, rng: Rng) -> None:
    """Run every recorded-noise pass, mutating ``company`` in place."""
    _inject_copy_paste(company, rng.child("copy-paste"))
    _plant_outliers(company, rng.child("outliers"))
    _plant_sod(company, rng.child("sod"))


def _add_extra(company: Company, identity_id: str, ent_id: str) -> None:
    company.ground_truth.extra_grants.setdefault(identity_id, [])
    if ent_id not in company.ground_truth.extra_grants[identity_id]:
        company.ground_truth.extra_grants[identity_id].append(ent_id)


# --- 5.1 copy-paste-user --------------------------------------------------


def _inject_copy_paste(company: Company, rng: Rng) -> None:
    cfg: GenConfig = company.config  # type: ignore[assignment]
    n = len(company.identities)
    if n < 4:
        return
    k = round(cfg.copy_paste_rate * n)
    if k <= 0:
        return
    # Templates: never-copied source identities drawn from the first half.
    idxs = list(range(n))
    rng.shuffle(idxs)
    copied = set(idxs[:k])
    updated = list(company.identities)
    for i in copied:
        r = rng.child(i)
        # pick a template that is not itself being copied
        for _ in range(8):
            src = r.randint(0, n - 1)
            if src != i and src not in copied:
                break
        else:
            continue
        updated[i] = replace(updated[i], copied_from=company.identities[src].id)
    company.identities = updated
    company._identity_by_id = None  # invalidate index


# --- 5.2 outliers ---------------------------------------------------------


def _plant_outliers(company: Company, rng: Rng) -> None:
    cfg: GenConfig = company.config  # type: ignore[assignment]
    identities = company.identities
    if not identities or not company.entitlements:
        return
    all_ids = list(company.all_entitlement_ids())

    # Entitlements reachable through ANY role (directly or transitively via
    # nested groups). Anything outside this set can only land on a peer through
    # rare random noise, so a planted grant of it is genuinely outlying.
    role_reachable: set[str] = set()
    for role in company.roles:
        for eid in role.entitlement_ids:
            role_reachable |= company.expand_group(eid)
    rare_pool = [eid for eid in all_ids if eid not in role_reachable]

    count = min(cfg.outlier_count, len(identities))
    victims = rng.sample(identities, count)
    for n, victim in enumerate(victims):
        r = rng.child(n)
        # Prefer a globally rare entitlement; fall back to any non-owned one.
        pool = rare_pool or [
            e for e in all_ids if e not in _role_bundle(company, victim)
        ]
        if not pool:
            continue
        pick = r.choice(pool)
        _add_extra(company, victim.id, pick)
        company.ground_truth.outliers.append(
            PlantedOutlier(
                identity_id=victim.id,
                entitlement_id=pick,
                reason="holds an entitlement not used by department peers",
            )
        )


# --- 5.3 SoD violations ---------------------------------------------------


def _plant_sod(company: Company, rng: Rng) -> None:
    cfg: GenConfig = company.config  # type: ignore[assignment]
    identities = company.identities
    leaves = [e for e in company.entitlements if not e.is_group]
    if len(identities) < 1 or len(leaves) < 2:
        return

    # Map a leaf → a group that (transitively) contains it, for "via nested".
    containing_group = _leaf_to_containing_group(company)

    count = min(cfg.sod_pair_count, len(identities))
    for n in range(count):
        r = rng.child(n)
        a, b = r.sample(leaves, 2)
        victim = r.choice(identities)
        rule = r.choice(_SOD_RULES)
        via = "direct"
        # Prefer a nested plant for ~half of pairs when a container exists.
        if r.chance(0.5) and b.id in containing_group:
            group_id = containing_group[b.id]
            _add_extra(company, victim.id, a.id)
            _add_extra(company, victim.id, group_id)
            via = "nested"
        else:
            _add_extra(company, victim.id, a.id)
            _add_extra(company, victim.id, b.id)
        company.ground_truth.sod_violations.append(
            PlantedSoD(
                id=derive_id("sod", n, width=4),
                rule=rule,
                entitlement_a=a.id,
                entitlement_b=b.id,
                identity_ids=(victim.id,),
                via=via,
            )
        )


# --- helpers --------------------------------------------------------------


def _role_bundle(company: Company, identity: Identity) -> set[str]:
    grants: set[str] = set()
    for rid in identity.role_ids:
        grants.update(company.role(rid).entitlement_ids)
    return grants


def _leaf_to_containing_group(company: Company) -> dict[str, str]:
    """Map each leaf entitlement id → some group whose expansion includes it."""
    mapping: dict[str, str] = {}
    for ent in company.entitlements:
        if not ent.is_group:
            continue
        for reached in company.expand_group(ent.id):
            if reached == ent.id:
                continue
            child = company.entitlement(reached)
            if not child.is_group and reached not in mapping:
                mapping[reached] = ent.id
    return mapping
