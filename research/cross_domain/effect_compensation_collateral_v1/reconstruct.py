from __future__ import annotations
import base64, hashlib, tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_SHA256 = "b4cfe9ad8416039573916b0afd0ddba2778b86c6e108f3504bc4240c77e8cf54"


def main() -> None:
    parts = sorted(HERE.glob("formal_bundle.b64.part*"))
    if len(parts) != 7:
        raise SystemExit(f"expected 7 base64 chunks, found {len(parts)}")
    encoded = "".join(part.read_text().strip() for part in parts)
    raw = base64.b64decode(encoded, validate=True)
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"archive hash mismatch: {actual}")
    archive = HERE / "formal_bundle.tar.gz"
    archive.write_bytes(raw)
    out = HERE / "reconstructed_evidence"
    out.mkdir(exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(out, filter="data")
    print(f"PASS_RECONSTRUCT {actual}")


if __name__ == "__main__":
    main()
