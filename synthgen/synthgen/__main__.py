"""Command-line entry point: ``python -m synthgen`` / ``synthgen``.

Generates a company and writes vendor-dialect exports plus the ground-truth file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import GenConfig, preset, tiers
from .dialects import available
from .generate import count_assignments, generate, write_company


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="synthgen",
        description="Generate a synthetic company with hidden ground truth.",
    )
    p.add_argument(
        "--tier",
        default="small",
        choices=tiers(),
        help="scale-tier preset (default: small)",
    )
    p.add_argument("--seed", type=int, default=0, help="PRNG seed (default: 0)")
    p.add_argument(
        "--out",
        type=Path,
        default=Path("./synthetic-company"),
        help="output directory (default: ./synthetic-company)",
    )
    p.add_argument(
        "--dialects",
        default=None,
        help=f"comma-separated dialects (available: {', '.join(available())})",
    )
    p.add_argument(
        "--summary-only",
        action="store_true",
        help="print counts without writing any files",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg: GenConfig = preset(args.tier).with_(seed=args.seed)
    if args.dialects:
        cfg = cfg.with_(dialects=tuple(d.strip() for d in args.dialects.split(",")))

    company = generate(cfg, seed=args.seed)

    print(f"tier={cfg.tier} seed={cfg.seed}")
    print(f"  identities   : {len(company.identities):,}")
    print(f"  applications : {len(company.applications):,}")
    print(f"  entitlements : {len(company.entitlements):,}")
    print(f"  roles        : {len(company.roles):,}")
    print(f"  assignments  : {count_assignments(company):,}")
    print(f"  outliers     : {len(company.ground_truth.outliers):,}")
    print(f"  sod          : {len(company.ground_truth.sod_violations):,}")

    if args.summary_only:
        return 0

    manifest = write_company(company, args.out)
    print(f"\nwrote exports to {args.out}")
    for name, paths in manifest["exports"].items():  # type: ignore[attr-defined]
        print(f"  {name}: {len(paths)} file(s)")
    print(f"  ground truth: {manifest['ground_truth']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
