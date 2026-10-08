#!/usr/bin/env python3
import argparse,base64,hashlib,json,pathlib,zlib

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("out"); a=ap.parse_args(); root=pathlib.Path(a.out)
 if root.exists(): raise SystemExit("destination exists")
 pub=json.loads(pathlib.Path("PUBLICATION.json").read_text()); chunks=[]
 for e in pub["ordered_parts"]:
  b=pathlib.Path(e["path"]).read_bytes()
  if len(b)!=e["bytes"] or hashlib.sha256(b).hexdigest()!=e["sha256"]: raise SystemExit("part mismatch")
  chunks.append(b.decode().strip())
 enc=base64.b64decode("".join(chunks))
 if hashlib.sha256(enc).hexdigest()!=pub["encoded_sha256"]: raise SystemExit("encoded mismatch")
 raw=zlib.decompress(enc)
 if hashlib.sha256(raw).hexdigest()!=pub["decoded_sha256"]: raise SystemExit("decoded mismatch")
 obj=json.loads(raw)
 if len(obj)!=pub["files"]: raise SystemExit("file count mismatch")
 root.mkdir()
 for rel,e in obj.items():
  p=pathlib.PurePosixPath(rel)
  if p.is_absolute() or ".." in p.parts: raise SystemExit("unsafe path")
  data=base64.b64decode(e["b64"])
  if hashlib.sha256(data).hexdigest()!=e["sha256"]: raise SystemExit("member mismatch")
  q=root/pathlib.Path(*p.parts); q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(data)
 print(json.dumps({"files":len(obj),"decoded_sha256":pub["decoded_sha256"]},sort_keys=True))
if __name__=="__main__": main()
