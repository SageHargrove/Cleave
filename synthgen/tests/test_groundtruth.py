"""Task 8.2 — ground-truth labels never leak into any vendor-dialect export."""

from __future__ import annotations

import json
from pathlib import Path

from synthgen.generate import write_company
from synthgen.groundtruth import find_leaks


def test_no_labels_leak_into_exports(small, tmp_path):
    write_company(small, tmp_path)
    assert find_leaks(small, tmp_path) == []


def test_ground_truth_written_to_distinct_path(small, tmp_path):
    manifest = write_company(small, tmp_path)
    gt_path = manifest["ground_truth"]
    assert gt_path.endswith("ground_truth.json")
    # not inside any dialect export directory
    for _name, paths in manifest["exports"].items():
        for p in paths:
            assert p != gt_path


def test_ground_truth_supports_scoring(small, tmp_path):
    manifest = write_company(small, tmp_path)
    doc = json.loads(Path(manifest["ground_truth"]).read_text(encoding="utf-8"))
    # stable ids + entitlement sets present for joins
    assert doc["roles"] and all(r["id"] and r["entitlement_ids"] for r in doc["roles"])
    assert all("identity_id" in o and "entitlement_id" in o for o in doc["outliers"])
    assert all(
        {"entitlement_a", "entitlement_b", "identity_ids"} <= s.keys()
        for s in doc["sod_violations"]
    )
