"""Task 5.5 — every planted SoD pair co-occurs; every planted outlier is rare
among its peers."""

from __future__ import annotations

from synthgen.assignments import effective_grants


def test_planted_sod_pairs_co_occur(small):
    by_id = {i.id: i for i in small.identities}
    assert small.ground_truth.sod_violations
    for sod in small.ground_truth.sod_violations:
        for iid in sod.identity_ids:
            eff = effective_grants(small, by_id[iid])
            assert sod.entitlement_a in eff, f"{sod.id}: missing a"
            assert sod.entitlement_b in eff, f"{sod.id}: missing b"


def test_nested_sod_reaches_via_group(small):
    # at least one SoD planted via nested group membership
    assert any(s.via == "nested" for s in small.ground_truth.sod_violations)


def test_planted_outliers_are_rare_among_peers(small):
    assert small.ground_truth.outliers
    by_id = {i.id: i for i in small.identities}
    for o in small.ground_truth.outliers:
        victim = by_id[o.identity_id]
        peers = [i for i in small.identities if i.department == victim.department]
        holders = sum(
            1 for p in peers if o.entitlement_id in effective_grants(small, p)
        )
        # rare: held by at most a small fraction of the peer group
        assert holders <= max(1, 0.15 * len(peers)), (
            f"outlier {o.entitlement_id} not rare: {holders}/{len(peers)} peers"
        )
        # and the victim genuinely holds it
        assert o.entitlement_id in effective_grants(small, victim)
