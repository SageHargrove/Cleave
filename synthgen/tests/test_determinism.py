"""Task 1.4 — same seed ⇒ identical output; different seed ⇒ different output."""

from __future__ import annotations

import os
import subprocess
import sys

from synthgen import generate, preset
from synthgen.generate import write_company
from synthgen.groundtruth import to_dict


def _read_all(root):
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_same_seed_identical_ground_truth():
    a = generate(preset("tiny"), seed=7)
    b = generate(preset("tiny"), seed=7)
    assert to_dict(a) == to_dict(b)


def test_same_seed_byte_identical_exports(tmp_path):
    a = generate(preset("tiny"), seed=7)
    b = generate(preset("tiny"), seed=7)
    da, db = tmp_path / "a", tmp_path / "b"
    write_company(a, da)
    write_company(b, db)
    assert _read_all(da) == _read_all(db)


_HASH_SEED_PROBE = """
import hashlib, json
from synthgen import generate, preset
from synthgen.groundtruth import to_dict
print(hashlib.sha256(
    json.dumps(to_dict(generate(preset("tiny"), seed=7)), sort_keys=True).encode()
).hexdigest())
"""


def test_same_seed_identical_across_processes():
    """The guarantee is (seed, config) ⇒ identical output, not per-process.

    Iterating a ``set[str]`` orders by string hash, which Python randomizes per
    process — so a set that reaches the output makes two runs of the *same*
    command disagree. Only a second process with a different PYTHONHASHSEED can
    catch it; in-process comparisons share one hash seed and always pass.
    """
    digests = set()
    for seed in ("1", "2"):
        proc = subprocess.run(
            [sys.executable, "-c", _HASH_SEED_PROBE],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        )
        digests.add(proc.stdout.strip())
    assert len(digests) == 1, "ground truth varies with PYTHONHASHSEED"


def test_different_seed_differs():
    a = generate(preset("tiny"), seed=7)
    b = generate(preset("tiny"), seed=8)
    assert to_dict(a) != to_dict(b)
    # identities themselves differ, not just labels
    assert [i.email for i in a.identities] != [i.email for i in b.identities]
