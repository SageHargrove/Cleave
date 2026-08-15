"""Org-structure generation: departments, titles, locations, manager chain,
hire/term dates, and the ~2% terminated-with-active-accounts fixture (tasks
2.1, 2.2).

The manager chain is acyclic by construction: an identity may only report to
one created earlier in the sequence, so cycles are impossible and every chain
terminates at the root (index 0).
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TypedDict

from .config import GenConfig
from .model import Identity
from .rng import Rng, derive_id


class _ManagerSlot(TypedDict):
    """A created identity still holding management-span capacity."""

    index: int
    id: str
    department: str
    level: int
    slots: int

# Small internal name pools — enough variety to look plausible, no external dep.
_FIRST = [
    "Alex",
    "Blair",
    "Casey",
    "Dana",
    "Ellis",
    "Frankie",
    "Gale",
    "Harper",
    "Ira",
    "Jules",
    "Kai",
    "Lee",
    "Morgan",
    "Noor",
    "Oakley",
    "Pat",
    "Quinn",
    "Riley",
    "Sage",
    "Toni",
    "Umi",
    "Val",
    "Wynn",
    "Xen",
    "Yael",
    "Zion",
    "Ari",
    "Bao",
    "Cruz",
    "Devi",
    "Emin",
    "Faye",
]
_LAST = [
    "Adler",
    "Bello",
    "Cho",
    "Diaz",
    "Eaton",
    "Fox",
    "Gupta",
    "Haas",
    "Imani",
    "Jain",
    "Kaur",
    "Lowe",
    "Mora",
    "Ng",
    "Ortiz",
    "Park",
    "Quan",
    "Ray",
    "Silva",
    "Tran",
    "Udo",
    "Vega",
    "Wu",
    "Xu",
    "Yoon",
    "Zhao",
    "Bauer",
    "Costa",
    "Doyle",
    "Ellis",
    "Frost",
    "Gomez",
]
_DEPARTMENTS = [
    "Finance",
    "Engineering",
    "Sales",
    "Human Resources",
    "IT",
    "Legal",
    "Operations",
    "Marketing",
    "Support",
    "Security",
]
# Title ladder by level (0 = executive). Index is clamped to the ladder length.
_TITLE_LADDER = [
    "Chief {d} Officer",
    "VP, {d}",
    "Director, {d}",
    "Senior Manager, {d}",
    "Manager, {d}",
    "Senior {d} Analyst",
    "{d} Analyst",
    "{d} Associate",
]
_LOCATIONS = [
    "New York, US",
    "Austin, US",
    "London, UK",
    "Berlin, DE",
    "Toronto, CA",
    "Singapore, SG",
    "Sydney, AU",
    "Remote",
]


def _iso(d: date) -> str:
    return d.isoformat()


def generate_identities(cfg: GenConfig, rng: Rng) -> tuple[list[Identity], set[int]]:
    """Build identities with an acyclic manager chain and hire/term dates.

    Returns the identities and the indices of the terminated-with-active-access
    subset (spec §8; ~2% of the population).
    """
    org_rng = rng.child("org")
    anchor = date.fromisoformat(cfg.anchor_date)
    n = cfg.n_identities

    # Managers-in-progress: created identities with remaining span capacity,
    # partitioned so a report always attaches to someone shallower than it.
    managers: list[_ManagerSlot] = []
    identities: list[Identity] = []

    # Pre-pick the terminated set and the terminated-with-active subset.
    n_term = round(cfg.terminated_fraction * n)
    n_term_active = max(1, round(cfg.terminated_with_active_fraction * n)) if n else 0
    idx_pool = list(range(n))
    org_rng.shuffle(idx_pool)
    terminated_idx = set(idx_pool[:n_term])
    # terminated-with-active is a subset of terminated
    term_active_idx = set(list(terminated_idx)[:n_term_active])

    for i in range(n):
        r = org_rng.child(i)
        emp_no = f"E{100000 + i}"
        ident_id = derive_id("emp", i)

        if i == 0 or not managers:
            manager = None
            level = 0
            department = r.choice(_DEPARTMENTS)
        else:
            mgr = r.choice(managers)
            manager = mgr
            level = mgr["level"] + 1
            # Mostly inherit manager's department; occasionally cross-report.
            department = mgr["department"] if r.chance(0.85) else r.choice(_DEPARTMENTS)

        title_tmpl = _TITLE_LADDER[min(level, len(_TITLE_LADDER) - 1)]
        title = title_tmpl.format(d=department)
        location = r.choice(_LOCATIONS)
        first = r.choice(_FIRST)
        last = r.choice(_LAST)
        email = f"{first}.{last}.{i}@example-corp.com".lower()

        # Hire 0–15 years before the anchor.
        hire = anchor - timedelta(days=r.randint(30, 365 * 15))
        terminated = i in terminated_idx
        term_date = None
        status = "active"
        if terminated:
            status = "terminated"
            # Terminated between hire and anchor.
            span = max((anchor - hire).days - 1, 1)
            term_date = _iso(hire + timedelta(days=r.randint(1, span)))

        ident = Identity(
            id=ident_id,
            employee_number=emp_no,
            first_name=first,
            last_name=last,
            email=email,
            department=department,
            title=title,
            location=location,
            hire_date=_iso(hire),
            status=status,
            manager_id=manager["id"] if manager else None,
            term_date=term_date,
        )
        identities.append(ident)

        # Consume a management slot and register this identity as a potential
        # manager (bounded span keeps the tree from going wide-and-flat).
        if manager is not None:
            manager["slots"] -= 1
            if manager["slots"] <= 0:
                managers.remove(manager)
        managers.append(
            {
                "index": i,
                "id": ident_id,
                "department": department,
                "level": level,
                "slots": r.randint(2, cfg.max_span_of_control),
            }
        )

    return identities, term_active_idx


def terminated_with_active_ids(
    identities: list[Identity], term_active_idx: set[int]
) -> list[str]:
    """Identity ids that are terminated yet retain active accounts."""
    return [identities[i].id for i in sorted(term_active_idx) if i < len(identities)]
