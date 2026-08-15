"""A thin predicted-vs-ground-truth scorer (task 8.3, design D6 / spec §8).

Deliberately minimal — enough for downstream ``engine`` golden tests to assert
recovery of planted structure. The full scoring harness lives with ``engine``.
Everything works on sets of stable-ID tuples so any finding type can be scored
by projecting it to comparable tuples.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable
from dataclasses import dataclass

from .model import Company


@dataclass(frozen=True)
class Score:
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 1.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 1.0

    @property
    def f_score(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def as_dict(self) -> dict[str, float | int]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "fn": self.fn,
            "precision": round(self.precision, 6),
            "recall": round(self.recall, 6),
            "f_score": round(self.f_score, 6),
        }


def prf(predicted: Iterable[Hashable], truth: Iterable[Hashable]) -> Score:
    """Precision/recall/F-score of a predicted set against a truth set."""
    p, t = set(predicted), set(truth)
    tp = len(p & t)
    return Score(tp=tp, fp=len(p - t), fn=len(t - p))


# --- projections of ground truth to comparable tuple sets -----------------


def outlier_truth(company: Company) -> set[tuple[str, str]]:
    """Planted outliers as ``(identity_id, entitlement_id)`` pairs."""
    return {(o.identity_id, o.entitlement_id) for o in company.ground_truth.outliers}


def sod_truth(company: Company) -> set[tuple[str, frozenset[str]]]:
    """Planted SoD violations as ``(identity_id, {ent_a, ent_b})`` pairs."""
    out: set[tuple[str, frozenset[str]]] = set()
    for s in company.ground_truth.sod_violations:
        pair = frozenset((s.entitlement_a, s.entitlement_b))
        for iid in s.identity_ids:
            out.add((iid, pair))
    return out


def role_membership_truth(company: Company) -> set[tuple[str, str]]:
    """Planted role membership as ``(identity_id, role_id)`` pairs."""
    return {(iid, r.id) for r in company.ground_truth.roles for iid in r.member_ids}
