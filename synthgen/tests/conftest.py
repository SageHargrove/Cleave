"""Shared fixtures.

Both companies are module-scoped: generation is deterministic and pure, so one
instance per module is safe to share and keeps the suite fast.
"""

from __future__ import annotations

import pytest

from synthgen import generate, preset


@pytest.fixture(scope="module")
def tiny():
    return generate(preset("tiny"), seed=1)


@pytest.fixture(scope="module")
def small():
    return generate(preset("small"), seed=1)
