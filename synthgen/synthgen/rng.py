"""Deterministic PRNG plumbing (design D2).

A single seed produces the whole company. Randomness is drawn only from
``Rng`` instances that descend from that seed via :meth:`Rng.child` — there is
no use of the global ``random`` module, no ``uuid4``, and no wall-clock time
anywhere in the data path. This guarantees NFR-6: same ``(seed, config)`` ⇒
byte-identical output.

IDs and GUID-style names are *derived* from the seed plus a stable key rather
than sampled, so they are reproducible regardless of generation order.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")

_MASK64 = (1 << 64) - 1


def _digest_int(*parts: object) -> int:
    """Stable 64-bit integer hash of ``parts`` (order-sensitive).

    Uses SHA-256 rather than the built-in ``hash()`` so results do not depend
    on ``PYTHONHASHSEED`` or the process.
    """
    h = hashlib.sha256(repr(parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


class Rng:
    """A seeded random stream that can spawn deterministic child streams."""

    __slots__ = ("seed", "_r")

    def __init__(self, seed: int) -> None:
        self.seed = seed & _MASK64
        self._r = random.Random(self.seed)

    def child(self, *key: object) -> Rng:
        """A new independent stream keyed by ``key`` under this stream's seed.

        Threading generation through named children (``rng.child("org")``)
        keeps unrelated parts of the pipeline from perturbing each other's
        sequences, so adding a feature does not reshuffle everything.
        """
        return Rng(_digest_int(self.seed, key))

    # -- thin, explicit delegations (no global state) --
    def random(self) -> float:
        return self._r.random()

    def randint(self, a: int, b: int) -> int:
        return self._r.randint(a, b)

    def uniform(self, a: float, b: float) -> float:
        return self._r.uniform(a, b)

    def choice(self, seq: Sequence[T]) -> T:
        return self._r.choice(seq)

    def choices(
        self, seq: Sequence[T], k: int, weights: Sequence[float] | None = None
    ) -> list[T]:
        return self._r.choices(seq, weights=weights, k=k)

    def sample(self, seq: Sequence[T], k: int) -> list[T]:
        return self._r.sample(seq, k)

    def shuffle(self, seq: list[T]) -> None:
        self._r.shuffle(seq)

    def chance(self, p: float) -> bool:
        """True with probability ``p`` (clamped to [0, 1])."""
        if p <= 0.0:
            return False
        if p >= 1.0:
            return True
        return self._r.random() < p


def derive_id(prefix: str, index: int, width: int = 6) -> str:
    """Deterministic zero-padded id, e.g. ``derive_id("emp", 42) -> 'emp_000042'``."""
    return f"{prefix}_{index:0{width}d}"


def derive_guid(*key: object) -> str:
    """Deterministic UUID-shaped string (no ``uuid4`` entropy).

    Entra emits GUID-named groups; we mimic the shape while staying
    reproducible by hashing ``key`` instead of drawing randomness.
    """
    h = hashlib.sha256(repr(key).encode("utf-8")).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
