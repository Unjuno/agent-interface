# Audit reconstruction only; not a new scientific allocation.
from pathlib import Path
import base64, hashlib, io, subprocess, sys, tarfile, tempfile

HERE=Path(__file__).resolve().parent
EXPECTED_BUNDLE="9bc7e05b1a54b67f26524fd4b93825f1b4e472cee32d4c6e8667a02263ce27d0"
EXPECTED_FORMAL="e99a808bab6288336251aa82eed0445864a1b62e2e25f20d9e1e5ef1c9673a71"
gz=base64.b64decode((HERE/"SOURCE_BUNDLE.b64").read_text(encoding="ascii"))
assert hashlib.sha256(gz).hexdigest()==EXPECTED_BUNDLE
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    with tarfile.open(fileobj=io.BytesIO(gz),mode="r:gz") as tf:
        tf.extractall(root)
    out=root/"FORMAL_RESULT.reconstructed.json"
    subprocess.run([sys.executable,str(root/"runner.py"),"formal",str(out)],cwd=root,check=True)
    got=hashlib.sha256(out.read_bytes()).hexdigest()
    assert got==EXPECTED_FORMAL,(got,EXPECTED_FORMAL)
    print(got)
