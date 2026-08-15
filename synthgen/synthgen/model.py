"""In-memory data model for a generated company (design D1/D3/D6).

Everything except the assignment *stream* lives here: identities, applications,
the entitlement catalog (with nested-group edges), accounts, and the hidden
ground truth. Assignments (target 5M) are never stored as a list — they are
derived per-identity on demand (see :mod:`synthgen.assignments`) so the
full-scale tier streams within memory budget (design D5).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Identity:
    id: str
    employee_number: str
    first_name: str
    last_name: str
    email: str
    department: str
    title: str
    location: str
    hire_date: str  # ISO date
    status: str  # "active" | "terminated"
    manager_id: str | None = None
    term_date: str | None = None  # ISO date, set iff terminated
    role_ids: tuple[str, ...] = ()  # ground-truth role membership
    copied_from: str | None = None  # copy-paste-user artifact source

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass(frozen=True)
class Entitlement:
    id: str
    app_id: str
    name: str
    kind: str  # "permission" | "group"
    contains: tuple[str, ...] = ()  # child entitlement ids (groups only)
    depth: int = 0  # nesting depth; 0 for leaf permissions

    @property
    def is_group(self) -> bool:
        return self.kind == "group"


@dataclass(frozen=True)
class Application:
    id: str
    name: str
    short_code: str
    vendor_hint: str
    entitlement_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Account:
    id: str
    app_id: str
    username: str
    identity_id: str | None = None  # None ⇒ orphan / uncorrelated
    disabled: bool = False
    last_login: str | None = None  # ISO date; None/old ⇒ dormant
    is_duplicate: bool = False


# --- ground-truth records (design D6) -------------------------------------


@dataclass(frozen=True)
class Role:
    id: str
    archetype: str
    department: str
    entitlement_ids: tuple[str, ...]  # the bundle a member "should" hold
    member_ids: tuple[str, ...] = ()  # intended members (ground truth)


@dataclass(frozen=True)
class PlantedOutlier:
    identity_id: str
    entitlement_id: str
    reason: str


@dataclass(frozen=True)
class PlantedSoD:
    id: str
    rule: str
    entitlement_a: str
    entitlement_b: str
    identity_ids: tuple[str, ...]
    via: str  # "direct" | "nested"


@dataclass(frozen=True)
class EffectivePath:
    """A transitively-reached entitlement and the group chain that grants it."""

    identity_id: str
    entitlement_id: str  # the effectively-held target
    path: tuple[str, ...]  # granted-group … → target (inclusive)


@dataclass
class GroundTruth:
    roles: list[Role] = field(default_factory=list)
    outliers: list[PlantedOutlier] = field(default_factory=list)
    sod_violations: list[PlantedSoD] = field(default_factory=list)
    effective_paths: list[EffectivePath] = field(default_factory=list)
    terminated_with_active: list[str] = field(default_factory=list)  # identity ids
    orphan_account_ids: list[str] = field(default_factory=list)
    terminated_account_ids: list[str] = field(default_factory=list)
    dormant_account_ids: list[str] = field(default_factory=list)
    duplicate_account_ids: list[str] = field(default_factory=list)
    # identity_id -> extra (planted/legacy) direct entitlement grants layered
    # on top of role-derived access. Kept explicit so invariants are exact.
    extra_grants: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Company:
    seed: int
    config: object  # GenConfig (avoids import cycle)
    identities: list[Identity] = field(default_factory=list)
    applications: list[Application] = field(default_factory=list)
    entitlements: list[Entitlement] = field(default_factory=list)
    accounts: list[Account] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    ground_truth: GroundTruth = field(default_factory=GroundTruth)

    # -- lazily-built indexes --
    _ent_by_id: dict[str, Entitlement] | None = field(default=None, repr=False)
    _identity_by_id: dict[str, Identity] | None = field(default=None, repr=False)
    _role_by_id: dict[str, Role] | None = field(default=None, repr=False)
    _all_ent_ids: tuple[str, ...] | None = field(default=None, repr=False)

    def all_entitlement_ids(self) -> tuple[str, ...]:
        if self._all_ent_ids is None:
            self._all_ent_ids = tuple(e.id for e in self.entitlements)
        return self._all_ent_ids

    def entitlement(self, ent_id: str) -> Entitlement:
        if self._ent_by_id is None:
            self._ent_by_id = {e.id: e for e in self.entitlements}
        return self._ent_by_id[ent_id]

    def identity(self, identity_id: str) -> Identity:
        if self._identity_by_id is None:
            self._identity_by_id = {i.id: i for i in self.identities}
        return self._identity_by_id[identity_id]

    def role(self, role_id: str) -> Role:
        if self._role_by_id is None:
            self._role_by_id = {r.id: r for r in self.roles}
        return self._role_by_id[role_id]

    def expand_group(self, ent_id: str) -> set[str]:
        """All leaf/entitlement ids reachable from ``ent_id`` (inclusive).

        Resolves nested-group membership transitively (FR-AN-8). The catalog is
        acyclic by construction, so a simple DFS terminates.
        """
        seen: set[str] = set()
        stack = [ent_id]
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            ent = self.entitlement(cur)
            stack.extend(ent.contains)
        return seen
