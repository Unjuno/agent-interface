from pathlib import Path
import base64,hashlib
root=Path(__file__).parent
s="".join("".join(p.read_text().split()) for p in sorted(root.glob("compact.part*.b64")))
b=base64.b64decode(s,validate=True)
assert hashlib.sha256(b).hexdigest()=="23e40db79137629c873b758e66ef97fc6b136a913243e52438d38020090e9b96"
out=root/"compact_evidence.tar.xz";out.write_bytes(b);print("23e40db79137629c873b758e66ef97fc6b136a913243e52438d38020090e9b96")
