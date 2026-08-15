"""Scoring helper (task 8.3) — precision/recall/F against ground truth."""

from __future__ import annotations

from synthgen import scoring


def test_prf_perfect():
    s = scoring.prf({1, 2, 3}, {1, 2, 3})
    assert s.precision == 1.0 and s.recall == 1.0 and s.f_score == 1.0


def test_prf_partial():
    s = scoring.prf({1, 2, 3, 4}, {1, 2, 5})
    assert s.tp == 2 and s.fp == 2 and s.fn == 1
    assert round(s.precision, 3) == 0.5
    assert round(s.recall, 3) == 0.667


def test_prf_empty_prediction():
    s = scoring.prf(set(), {1, 2})
    assert s.recall == 0.0
    assert s.precision == 1.0  # nothing predicted ⇒ no false positives


def test_perfect_recovery_scores_one(small):
    # Feeding the ground truth back to itself yields a perfect score.
    truth = scoring.outlier_truth(small)
    assert scoring.prf(truth, truth).f_score == 1.0
    sod = scoring.sod_truth(small)
    assert scoring.prf(sod, sod).f_score == 1.0
    roles = scoring.role_membership_truth(small)
    assert scoring.prf(roles, roles).f_score == 1.0
