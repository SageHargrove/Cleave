"""Task 3.4 — nesting depth is bounded; a purely-transitive access path exists."""

from __future__ import annotations

from synthgen.assignments import direct_grants


def test_nesting_depth_is_bounded(small):
    max_depth = small.config.max_nesting_depth
    assert any(e.is_group and e.contains for e in small.entitlements)
    for ent in small.entitlements:
        assert ent.depth <= max_depth


def test_group_to_group_edges_exist(small):
    # at least one group whose members include another group (nesting)
    ent_by_id = {e.id: e for e in small.entitlements}
    nested = [
        e
        for e in small.entitlements
        if e.is_group and any(ent_by_id[c].is_group for c in e.contains)
    ]
    assert nested, "expected at least one group nested inside another group"


def test_purely_transitive_access_path_exists(small):
    paths = small.ground_truth.effective_paths
    assert paths, "expected at least one recorded effective-access path"
    by_id = {i.id: i for i in small.identities}
    # validate one path: target reachable via the chain, not granted directly
    p = paths[0]
    ident = by_id[p.identity_id]
    direct = direct_grants(small, ident)
    assert p.entitlement_id not in direct
    assert p.path[0] in direct  # the chain starts at a directly-granted group
    # each hop is a real membership edge
    for parent, child in zip(p.path, p.path[1:], strict=False):
        assert child in small.entitlement(parent).contains
    assert p.path[-1] == p.entitlement_id
