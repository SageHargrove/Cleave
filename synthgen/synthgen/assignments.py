"""Per-identity grant derivation — the streamable heart of the generator.

Assignments are never materialized as a 5M-row list (design D5). Instead each
identity's grant set is *derived on demand* from stored state:

    role bundles  +  copy-paste inheritance  +  per-identity random noise
    +  planted extras (outliers / SoD / legacy, recorded in ground truth)

Because every layer is a pure function of ``(company.seed, identity.id, config)``
plus the small explicit ground-truth extras, any identity's grants can be
recomputed in isolation, so exporters can stream one identity at a time.
"""

from __future__ import annotations

from collections.abc import Iterator

from .config import GenConfig
from .model import Company, Identity
from .rng import Rng


def pre_noise_grants(company: Company, identity: Identity) -> set[str]:
    """The 'true' assignment set from roles alone (used for role-mining scoring)."""
    grants: set[str] = set()
    for rid in identity.role_ids:
        grants.update(company.role(rid).entitlement_ids)
    return grants


def _noise_grants(company: Company, identity: Identity) -> set[str]:
    """Generic, unlabeled noise: over-provisioning + legacy stale grants.

    Computed deterministically per identity (no stored state) so it costs no
    memory at scale. These are *not* individually recorded in ground truth —
    they are the haystack role mining must see through.
    """
    cfg: GenConfig = company.config  # type: ignore[assignment]
    r = Rng(company.seed).child("noise", identity.id)
    extra: set[str] = set()
    all_ids = company.all_entitlement_ids()
    if not all_ids:
        return extra
    if r.chance(cfg.over_provision_rate):
        for _ in range(r.randint(1, 4)):
            extra.add(r.choice(all_ids))
    if r.chance(cfg.legacy_grant_rate):
        for _ in range(r.randint(1, 2)):
            extra.add(r.choice(all_ids))
    return extra


def direct_grants(company: Company, identity: Identity) -> set[str]:
    """Observed (post-noise) direct entitlement grants for an identity.

    This is what the vendor dialects export (groups stay as groups — importers
    resolve effective access). Order-independent set.
    """
    grants = pre_noise_grants(company, identity)
    if identity.copied_from:
        # Copy-paste-user artifact: cloned from a template peer's role access.
        src = company.identity(identity.copied_from)
        grants.update(pre_noise_grants(company, src))
    grants |= _noise_grants(company, identity)
    grants.update(company.ground_truth.extra_grants.get(identity.id, ()))
    return grants


def effective_grants(company: Company, identity: Identity) -> set[str]:
    """All entitlements the identity effectively holds (groups expanded)."""
    eff: set[str] = set()
    for eid in direct_grants(company, identity):
        eff |= company.expand_group(eid)
    return eff


def transitive_paths(
    company: Company, identity: Identity
) -> list[tuple[str, tuple[str, ...]]]:
    """Entitlements reachable ONLY through nested groups, with their paths.

    Returns ``(target_ent_id, path)`` pairs where ``target`` is not directly
    granted but is reachable by descending group membership. ``path`` runs from
    the directly-granted group down to (and including) the target.
    """
    direct = direct_grants(company, identity)
    results: list[tuple[str, tuple[str, ...]]] = []
    # Sorted, not raw set order: string-set iteration is PYTHONHASHSEED-
    # dependent, and these paths reach ground_truth.json — where the generator
    # promises byte-identical output for a given (seed, config) (NFR-6). Under
    # the recorded-path cap it would change the *content*, not just the order.
    for start in sorted(direct):
        ent = company.entitlement(start)
        if not ent.is_group:
            continue
        # DFS keeping the path; record targets not held directly.
        stack: list[tuple[str, tuple[str, ...]]] = [(start, (start,))]
        seen: set[str] = set()
        while stack:
            cur, path = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            if cur != start and cur not in direct:
                results.append((cur, path))
            for child in company.entitlement(cur).contains:
                stack.append((child, path + (child,)))
    return results


def iter_identity_grants(
    company: Company,
) -> Iterator[tuple[Identity, list[str]]]:
    """Yield ``(identity, sorted_direct_grant_ids)`` one identity at a time.

    The generator form is what lets exporters stream the assignment table
    without ever holding all rows in memory.
    """
    for ident in company.identities:
        yield ident, sorted(direct_grants(company, ident))
