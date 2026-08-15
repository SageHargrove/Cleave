"""Task 4.3 — pre-noise, every intended role member holds exactly that role's
entitlements."""

from __future__ import annotations

from synthgen.assignments import pre_noise_grants


def test_pre_noise_members_hold_role_bundle(small):
    by_id = {i.id: i for i in small.identities}
    assert small.roles
    for role in small.roles:
        bundle = set(role.entitlement_ids)
        assert role.member_ids, f"role {role.id} has no members"
        for member_id in role.member_ids:
            grants = pre_noise_grants(small, by_id[member_id])
            missing = bundle - grants
            assert not missing, f"{member_id} missing {missing} from {role.id}"


def test_every_identity_has_at_least_one_role(small):
    for ident in small.identities:
        assert ident.role_ids, f"{ident.id} has no role"
