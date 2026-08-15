"""Hidden ground-truth roles and identity→role mapping (tasks 4.1–4.2, design D1).

A role is a job archetype paired with an entitlement bundle a member "should"
hold. Identities are mapped to one or more roles (biased by department). The
pre-noise "true" assignment set — used both to export access and to score role
mining — is the union of a member's role bundles; noise is layered on later.
"""

from __future__ import annotations

from dataclasses import replace

from .config import GenConfig
from .model import Entitlement, Identity, Role
from .rng import Rng, derive_id

_ARCHETYPES = [
    "Clerk",
    "Analyst",
    "Approver",
    "Administrator",
    "Manager",
    "Auditor",
    "Engineer",
    "Specialist",
    "Coordinator",
    "Lead",
]


def bundle_size(cfg: GenConfig) -> int:
    """Target entitlements per role, sized so total ≈ ``target_assignments``.

    direct grants ≈ union of ``max_roles_per_identity`` bundles, so a bundle
    of ``target / identities / roles-per-person`` lands total assignments near
    the configured target.
    """
    per_person = max(3, cfg.target_assignments // max(1, cfg.n_identities))
    return max(3, per_person // max(1, cfg.max_roles_per_identity))


def generate_roles(
    cfg: GenConfig, rng: Rng, entitlements: list[Entitlement]
) -> list[Role]:
    """Define ``n_roles`` hidden roles, each a bundle drawn from the catalog."""
    role_rng = rng.child("roles")
    ent_ids = [e.id for e in entitlements]
    group_ids = [e.id for e in entitlements if e.is_group]
    size = min(bundle_size(cfg), max(3, len(ent_ids)))

    departments = _departments()
    roles: list[Role] = []
    for i in range(cfg.n_roles):
        r = role_rng.child(i)
        dept = departments[i % len(departments)]
        archetype = f"{dept}/{r.choice(_ARCHETYPES)}"
        bundle = set(r.sample(ent_ids, min(size, len(ent_ids))))
        # Ensure at least one group is in the bundle so effective access must be
        # resolved transitively (FR-AN-8) for that role's members.
        if group_ids and not any(gid in bundle for gid in group_ids):
            bundle.add(r.choice(group_ids))
        roles.append(
            Role(
                id=derive_id("role", i, width=4),
                archetype=archetype,
                department=dept,
                entitlement_ids=tuple(sorted(bundle)),
            )
        )
    return roles


def assign_roles(
    cfg: GenConfig, rng: Rng, identities: list[Identity], roles: list[Role]
) -> tuple[list[Identity], list[Role]]:
    """Map each identity to 1–``max_roles_per_identity`` roles (dept-biased).

    Returns updated identities (with ``role_ids`` set) and updated roles (with
    ``member_ids`` populated for the ground-truth file).
    """
    map_rng = rng.child("role-assign")
    by_dept: dict[str, list[Role]] = {}
    for role in roles:
        by_dept.setdefault(role.department, []).append(role)

    members: dict[str, list[str]] = {role.id: [] for role in roles}
    updated: list[Identity] = []
    for ident in identities:
        r = map_rng.child(ident.id)
        n = r.randint(1, cfg.max_roles_per_identity)
        # Prefer roles in the identity's department; fall back to any role.
        pool = by_dept.get(ident.department) or roles
        picks = _pick_roles(r, pool, roles, n)
        rid_tuple = tuple(
            dict.fromkeys(role.id for role in picks)
        )  # dedupe, keep order
        for rid in rid_tuple:
            members[rid].append(ident.id)
        updated.append(replace(ident, role_ids=rid_tuple))

    updated_roles = [
        replace(role, member_ids=tuple(members[role.id])) for role in roles
    ]
    return updated, updated_roles


def _pick_roles(r: Rng, pool: list[Role], all_roles: list[Role], n: int) -> list[Role]:
    picks: list[Role] = []
    for _ in range(n):
        source = pool if r.chance(0.8) and pool else all_roles
        picks.append(r.choice(source))
    return picks


def _departments() -> list[str]:
    # Kept in sync with org._DEPARTMENTS via import to avoid drift.
    from .org import _DEPARTMENTS

    return list(_DEPARTMENTS)
