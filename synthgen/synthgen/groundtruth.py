"""Ground-truth finalization, serialization, and leak checking (tasks 3.3, 8.1, 8.2).

The ground-truth file is the one artifact only *we* have. It is written to a
distinct path, never mixed into vendor exports, and carries stable IDs so a
scorer can join predicted findings to planted truth (design D6).
"""

from __future__ import annotations

import json
from pathlib import Path

from .assignments import transitive_paths
from .model import Company, EffectivePath

# Cap recorded effective-access paths so the artifact stays bounded at scale
# while still guaranteeing the transitive-access scenario is represented.
_MAX_EFFECTIVE_PATHS = 500


def finalize_ground_truth(company: Company, term_active_ids: list[str]) -> None:
    """Populate derived ground-truth fields after all structure is planted."""
    gt = company.ground_truth
    gt.roles = list(company.roles)
    gt.terminated_with_active = list(term_active_ids)

    # Record a bounded sample of purely-transitive access paths (FR-AN-8).
    recorded = 0
    for ident in company.identities:
        if recorded >= _MAX_EFFECTIVE_PATHS:
            break
        for target, path in transitive_paths(company, ident):
            gt.effective_paths.append(
                EffectivePath(identity_id=ident.id, entitlement_id=target, path=path)
            )
            recorded += 1
            if recorded >= _MAX_EFFECTIVE_PATHS:
                break


def to_dict(company: Company) -> dict[str, object]:
    """Machine-readable ground-truth document (design D6)."""
    gt = company.ground_truth
    return {
        "schema_version": 1,
        "seed": company.seed,
        "tier": getattr(company.config, "tier", None),
        "roles": [
            {
                "id": r.id,
                "archetype": r.archetype,
                "department": r.department,
                "entitlement_ids": list(r.entitlement_ids),
                "member_ids": list(r.member_ids),
            }
            for r in gt.roles
        ],
        "outliers": [
            {
                "identity_id": o.identity_id,
                "entitlement_id": o.entitlement_id,
                "reason": o.reason,
            }
            for o in gt.outliers
        ],
        "sod_violations": [
            {
                "id": s.id,
                "rule": s.rule,
                "entitlement_a": s.entitlement_a,
                "entitlement_b": s.entitlement_b,
                "identity_ids": list(s.identity_ids),
                "via": s.via,
            }
            for s in gt.sod_violations
        ],
        "effective_paths": [
            {
                "identity_id": p.identity_id,
                "entitlement_id": p.entitlement_id,
                "path": list(p.path),
            }
            for p in gt.effective_paths
        ],
        "terminated_with_active": list(gt.terminated_with_active),
        "orphan_account_ids": list(gt.orphan_account_ids),
        "terminated_account_ids": list(gt.terminated_account_ids),
        "dormant_account_ids": list(gt.dormant_account_ids),
        "duplicate_account_ids": list(gt.duplicate_account_ids),
    }


def write_ground_truth(company: Company, path: str | Path) -> Path:
    """Write the ground-truth JSON to ``path`` and return it."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(to_dict(company), fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def leak_markers(company: Company) -> list[str]:
    """Tokens that must never appear in any vendor-dialect export file."""
    gt = company.ground_truth
    markers = {"ground_truth", "member_ids", "effective_path"}
    markers.update(r.id for r in gt.roles)
    markers.update(r.archetype for r in gt.roles)
    markers.update(s.id for s in gt.sod_violations)
    markers.update(s.rule for s in gt.sod_violations)
    markers.update(o.reason for o in gt.outliers)
    return sorted(m for m in markers if m)


def find_leaks(company: Company, export_dir: str | Path) -> list[tuple[str, str]]:
    """Return ``(file, marker)`` pairs where a ground-truth token leaked."""
    export_dir = Path(export_dir)
    markers = leak_markers(company)
    hits: list[tuple[str, str]] = []
    for file in sorted(export_dir.rglob("*")):
        if not file.is_file():
            continue
        if file.name == "ground_truth.json":
            continue  # the ground-truth artifact is expected to contain markers
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for marker in markers:
            if marker and marker in text:
                hits.append((str(file), marker))
    return hits
