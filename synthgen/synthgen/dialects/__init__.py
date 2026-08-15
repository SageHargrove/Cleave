"""Vendor-dialect emitters (design D4).

Each dialect writes the *same* company as one vendor's export files, differing
in column names, casing, delimiter, multi-value conventions, and messy-file
quirks. Adding a vendor is one :class:`~synthgen.dialects.base.Dialect`
subclass.
"""

from __future__ import annotations

from .ad import ADDialect
from .base import Dialect
from .entra import EntraDialect
from .sailpoint import SailPointDialect

_REGISTRY: dict[str, type[Dialect]] = {
    "sailpoint": SailPointDialect,
    "entra": EntraDialect,
    "ad": ADDialect,
}


def get_dialect(name: str) -> Dialect:
    try:
        return _REGISTRY[name]()
    except KeyError:
        raise ValueError(
            f"unknown dialect {name!r}; known: {sorted(_REGISTRY)}"
        ) from None


def available() -> list[str]:
    return sorted(_REGISTRY)


__all__ = [
    "Dialect",
    "SailPointDialect",
    "EntraDialect",
    "ADDialect",
    "get_dialect",
    "available",
]
