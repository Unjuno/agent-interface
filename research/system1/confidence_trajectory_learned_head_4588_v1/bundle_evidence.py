"""Losslessly archive each raw seed evidence document and record SHA-256."""
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    root=Path("outputs/formal01");training=root/"training";dest=root/"bundles";dest.mkdir(exist_ok=True)
    items=[]
    for evidence in sorted(training.glob("seed-*/evidence.json")):
        seed=evidence.parent.name.removeprefix("seed-"); target=dest/f"seed-{seed}.zip"
        with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            z.write(evidence,"evidence.json")
        data=target.read_bytes()
        items.append({"seed":int(seed),"path":target.name,"bytes":len(data),
                      "sha256":hashlib.sha256(data).hexdigest(),
                      "evidence_sha256":hashlib.sha256(evidence.read_bytes()).hexdigest()})
    manifest={"schema":"confidence-trajectory-evidence-bundles-v1","items":items,
              "total_bytes":sum(x["bytes"] for x in items)}
    (dest/"EVIDENCE_MANIFEST.json").write_text(
        json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    print(json.dumps(manifest,sort_keys=True))


if __name__=="__main__":main()
