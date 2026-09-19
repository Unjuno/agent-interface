import hashlib
from pathlib import Path

from verify_preregistration import stable_sha256


def test_stable_sha256_ignores_windows_newlines(tmp_path: Path):
    path = tmp_path / "source.py"
    path.write_bytes(b"a\r\nb\r\n")
    assert stable_sha256(path) == hashlib.sha256(b"a\nb\n").hexdigest()
