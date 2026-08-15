"""Deterministic synthetic identity and entitlement data generator.

Generates a fake company (identities, applications, entitlements with nested
groups, accounts, and assignments) from hidden ground-truth roles plus noise,
emitted in multiple vendor dialects alongside a separate machine-readable
ground-truth file for objective algorithm scoring.

Same (seed, config) always produces byte-identical output.

Public entry points::

    from synthgen import generate, GenConfig, preset
    company = generate(preset("tiny"), seed=1)
"""

from __future__ import annotations

from .config import GenConfig, preset, tiers
from .generate import count_assignments, generate, write_company
from .model import Company

__all__ = [
    "GenConfig",
    "preset",
    "tiers",
    "generate",
    "write_company",
    "count_assignments",
    "Company",
]
