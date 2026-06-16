"""Golden-output gates for shared_core convergence candidates.

These tests pin the *current* numeric/string outputs of the ingestion service's
local helpers against the equivalent ``shared_core`` implementations. They make
any future swap to ``shared_core`` a safe, golden-gated refactor: if a swap ever
changes an output, one of these assertions fails.
"""

from app.processing.deduplication import compute_hash
from shared_core import docparse as sc_docparse


def test_compute_hash_matches_shared_core() -> None:
    """Local ``compute_hash`` is byte-identical to ``shared_core.docparse``.

    This is a clean convergence target: the implementations already produce the
    same SHA-256 hex digest, so ingestion could delegate to ``shared_core``
    without changing any persisted content hash.
    """
    samples = ["", "hello world", "a" * 1000, "unicode: café ☕", "line1\nline2"]
    for sample in samples:
        assert compute_hash(sample) == sc_docparse.compute_hash(sample)


def test_compute_hash_golden_values() -> None:
    # Pinned digests guard against any silent change to the hashing scheme.
    assert compute_hash("knowledgeops") == (
        "26a5b6bcafeab986b6d65310687ddfb73d59bde78e518884ed6722bef539b7f0"
    )
    assert compute_hash("hello world") == (
        "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    )
