"""Generation configuration and scale-tier presets (task 1.2).

``GenConfig`` is the single knob-set that, together with a seed, fully
determines a company. Presets range from ``tiny`` (dozens of identities, for
fast unit tests) to ``full`` (the §6 NFR targets: 50k identities, 100k
accounts, 25k entitlements, 5M assignments).
"""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class GenConfig:
    """Everything (besides the seed) that determines a generated company."""

    tier: str = "small"

    # -- scale --
    n_identities: int = 2_000
    n_applications: int = 20
    n_entitlements: int = 1_500
    target_assignments: int = 60_000

    # -- org --
    terminated_fraction: float = 0.08
    terminated_with_active_fraction: float = (
        0.02  # of all identities (subset of terminated)
    )
    max_span_of_control: int = 8

    # -- entitlement catalog / nesting (D3) --
    group_fraction: float = 0.30  # fraction of entitlements that are groups
    max_nesting_depth: int = 4
    guid_group_fraction: float = 0.25  # of groups, named as Entra-style GUIDs

    # -- ground-truth roles (D1) --
    n_roles: int = 40
    max_roles_per_identity: int = 2

    # -- noise rates (D1) --
    over_provision_rate: float = 0.05  # extra entitlements sprinkled per identity
    legacy_grant_rate: float = 0.03  # stale grants from prior roles
    copy_paste_rate: float = 0.02  # identities cloned from a "template" peer
    outlier_count: int = 20  # planted rare-access outliers
    sod_pair_count: int = 12  # planted toxic entitlement pairs
    orphan_account_count: int = 15  # accounts with no owning identity
    dormant_fraction: float = 0.06  # accounts with no recent login
    duplicate_account_count: int = 15  # a person with two accounts on one app

    # -- dialects (D4) --
    dialects: tuple[str, ...] = ("sailpoint", "entra", "ad")

    # -- streaming (D5) --
    chunk_size: int = 50_000

    # -- world clock --
    # Fixed "now" for the synthetic world. Using a constant (not wall-clock)
    # keeps hire/term/login dates reproducible (NFR-6).
    anchor_date: str = "2025-01-01"

    # -- provenance --
    seed: int = 0

    def with_(self, **changes: object) -> GenConfig:
        """Return a copy with fields overridden (e.g. ``cfg.with_(seed=7)``)."""
        return replace(self, **changes)  # type: ignore[arg-type]


# --- scale-tier presets ---------------------------------------------------

_PRESETS: dict[str, GenConfig] = {
    # Dozens of identities; every planted structure type still present.
    "tiny": GenConfig(
        tier="tiny",
        n_identities=40,
        n_applications=10,
        n_entitlements=80,
        target_assignments=600,
        n_roles=6,
        outlier_count=3,
        sod_pair_count=2,
        orphan_account_count=2,
        duplicate_account_count=2,
        chunk_size=1_000,
    ),
    # A few thousand identities; realistic-ish, still fast.
    "small": GenConfig(tier="small"),
    # The §6 NFR targets.
    "full": GenConfig(
        tier="full",
        n_identities=50_000,
        n_applications=40,
        n_entitlements=25_000,
        target_assignments=5_000_000,
        n_roles=200,
        outlier_count=400,
        sod_pair_count=120,
        orphan_account_count=300,
        duplicate_account_count=300,
        chunk_size=100_000,
    ),
}


def preset(name: str) -> GenConfig:
    """Return the named scale-tier preset (``tiny`` / ``small`` / ``full``)."""
    try:
        return _PRESETS[name]
    except KeyError:
        raise ValueError(
            f"unknown tier {name!r}; choose from {sorted(_PRESETS)}"
        ) from None


def tiers() -> list[str]:
    return sorted(_PRESETS)
