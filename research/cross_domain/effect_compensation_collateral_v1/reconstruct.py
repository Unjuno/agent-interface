from __future__ import annotations
import base64, hashlib, tarfile
from pathlib import Path

B64 = Path(__file__).with_name("formal_bundle.tar.gz.b64")
EXPECTED_SHA256 = "b4cfe9ad8416039573916b0afd0ddba2778b86c6e108f3504bc4240c77e8cf54"

def main() -> None:
    raw = base64.b64decode(B64.read_text())
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"archive hash mismatch: {actual}")
    archive = B64.with_name("formal_bundle.tar.gz")
    archive.write_bytes(raw)
    out = B64.with_name("reconstructed_evidence")
    out.mkdir(exist_ok=True)
    with tarfile.open(archive, "r:gz") as tf:
        tf.extractall(out, filter="data")
    print(f"PASS_RECONSTRUCT {actual}")

if __name__ == "__main__":
    main()
