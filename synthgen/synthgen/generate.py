"""The generation pipeline: ``(config, seed) -> Company`` and export writing.

Order mirrors design D1: build the true org and hidden roles, apply roles to
produce true access, then layer noise/planted findings on top, then finalize and
export. Assignments are streamed to disk one identity at a time (design D5).
"""

from __future__ import annotations

from pathlib import Path

from . import accounts, catalog, groundtruth, noise, org, roles
from .assignments import direct_grants
from .config import GenConfig, preset
from .dialects import get_dialect
from .model import Company, GroundTruth
from .rng import Rng


def generate(config: GenConfig | None = None, seed: int | None = None) -> Company:
    """Generate a full company deterministically from ``(config, seed)``.

    ``seed`` overrides ``config.seed`` when given; otherwise the config's seed
    is used. Same inputs ⇒ identical company and ground truth (NFR-6).
    """
    cfg = config or preset("small")
    if seed is not None:
        cfg = cfg.with_(seed=seed)
    rng = Rng(cfg.seed)

    # 1. Org (true structure).
    identities, term_active_idx = org.generate_identities(cfg, rng)
    term_active_ids = org.terminated_with_active_ids(identities, term_active_idx)

    # 2. Catalog + nested groups.
    applications, entitlements = catalog.generate_catalog(cfg, rng)

    # 3. Hidden ground-truth roles, then map identities to them.
    role_list = roles.generate_roles(cfg, rng, entitlements)
    identities, role_list = roles.assign_roles(cfg, rng, identities, role_list)

    company = Company(
        seed=cfg.seed,
        config=cfg,
        identities=identities,
        applications=applications,
        entitlements=entitlements,
        accounts=[],
        roles=role_list,
        ground_truth=GroundTruth(),
    )

    # 4. Noise + planted, labeled findings (mutates ground truth in place).
    noise.inject_noise(company, rng)

    # 5. Accounts, including hygiene fixtures.
    accounts.generate_accounts(company, rng, term_active_ids)

    # 6. Finalize derived ground truth (effective paths, term-with-active).
    groundtruth.finalize_ground_truth(company, term_active_ids)

    return company


def count_assignments(company: Company) -> int:
    """Count direct assignments by streaming — never materializes the table."""
    total = 0
    for ident in company.identities:
        total += len(direct_grants(company, ident))
    return total


def write_company(company: Company, out_dir: str | Path) -> dict[str, object]:
    """Write every enabled dialect plus the ground-truth file under ``out_dir``.

    Returns a manifest of written paths.
    """
    out_dir = Path(out_dir)
    cfg: GenConfig = company.config  # type: ignore[assignment]
    exports: dict[str, list[str]] = {}
    manifest: dict[str, object] = {"exports": exports, "ground_truth": None}

    for name in cfg.dialects:
        paths = get_dialect(name).emit(company, out_dir)
        exports[name] = [str(p) for p in paths]

    gt_path = groundtruth.write_ground_truth(company, out_dir / "ground_truth.json")
    manifest["ground_truth"] = str(gt_path)
    return manifest
