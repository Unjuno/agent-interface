import base64,hashlib,json,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;m=json.loads((H/"RESULT_PUBLICATION_MANIFEST.json").read_text());chunks=[]
for x in m["parts"]:
 b=(H/x["name"]).read_bytes();assert len(b)==x["bytes"] and hashlib.sha256(b).hexdigest()==x["sha256"];chunks.append(b)
b64=b"".join(chunks);assert hashlib.sha256(b64).hexdigest()==m["archive_concat_sha256"];raw=base64.b64decode(b64);assert hashlib.sha256(raw).hexdigest()==m["archive_binary_sha256"];p=H/"RESULT_ARCHIVE_A2.tar.gz";p.write_bytes(raw)
with tarfile.open(p,"r:gz") as t:t.extractall(H/"reconstructed_result_a2")
print("PASS_RECONSTRUCT_RESULT_A2",m["members"])
