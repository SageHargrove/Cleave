"""Account generation, including labeled hygiene fixtures (task 5.4).

Only *notable* accounts are materialized as :class:`Account` records: the
per-identity primary account plus the planted hygiene cases (orphan/uncorrelated,
dormant, duplicate) and the terminated-with-active fixtures. The dense
per-(identity, app) accounts implied by the assignment stream are derived at
export time (see :func:`derived_username`) rather than stored, keeping memory
bounded at scale.
"""

from __future__ import annotations

from datetime import date, timedelta

from .config import GenConfig
from .model import Account, Company, Identity
from .rng import Rng, derive_id


def derived_username(identity: Identity, app_short_code: str) -> str:
    """Deterministic per-(identity, app) account name used by exporters."""
    stem = f"{identity.first_name[0]}{identity.last_name}.{identity.employee_number}"
    return stem.lower()


def generate_accounts(company: Company, rng: Rng, term_active_ids: list[str]) -> None:
    """Create primary + hygiene accounts and record hygiene lists in ground truth."""
    cfg: GenConfig = company.config  # type: ignore[assignment]
    acct_rng = rng.child("accounts")
    anchor = date.fromisoformat(cfg.anchor_date)
    gt = company.ground_truth
    accounts: list[Account] = []
    idx = 0

    term_active_set = set(term_active_ids)

    # Primary account per identity.
    for ident in company.identities:
        r = acct_rng.child(ident.id)
        acct_id = derive_id("acct", idx)
        idx += 1
        disabled = ident.status == "terminated"
        # terminated-with-active override: account stays enabled despite term.
        if ident.id in term_active_set:
            disabled = False
        # dormant: no login in a long time
        dormant = r.chance(cfg.dormant_fraction)
        if dormant:
            last_login = (anchor - timedelta(days=r.randint(200, 900))).isoformat()
        else:
            last_login = (anchor - timedelta(days=r.randint(0, 45))).isoformat()

        accounts.append(
            Account(
                id=acct_id,
                app_id="app_000",
                username=derived_username(ident, "PRIMARY"),
                identity_id=ident.id,
                disabled=disabled,
                last_login=last_login,
            )
        )
        if disabled and ident.status == "terminated":
            gt.terminated_account_ids.append(acct_id)
        if ident.id in term_active_set:
            gt.terminated_account_ids.append(acct_id)  # terminated person, active acct
        if dormant:
            gt.dormant_account_ids.append(acct_id)

    # Orphan / uncorrelated accounts (no owning identity).
    for n in range(cfg.orphan_account_count):
        r = acct_rng.child("orphan", n)
        acct_id = derive_id("acct", idx)
        idx += 1
        accounts.append(
            Account(
                id=acct_id,
                app_id="app_000",
                username=f"svc-{r.choice(['batch', 'sync', 'legacy', 'temp'])}-{n:03d}",
                identity_id=None,
                disabled=r.chance(0.3),
                last_login=(anchor - timedelta(days=r.randint(0, 600))).isoformat(),
            )
        )
        gt.orphan_account_ids.append(acct_id)

    # Duplicate accounts: a second account for an existing identity on one app.
    if company.identities:
        for n in range(cfg.duplicate_account_count):
            r = acct_rng.child("dup", n)
            owner = r.choice(company.identities)
            acct_id = derive_id("acct", idx)
            idx += 1
            accounts.append(
                Account(
                    id=acct_id,
                    app_id="app_000",
                    username=derived_username(owner, "PRIMARY") + f"-alt{n}",
                    identity_id=owner.id,
                    disabled=False,
                    last_login=(anchor - timedelta(days=r.randint(0, 120))).isoformat(),
                    is_duplicate=True,
                )
            )
            gt.duplicate_account_ids.append(acct_id)

    company.accounts = accounts
