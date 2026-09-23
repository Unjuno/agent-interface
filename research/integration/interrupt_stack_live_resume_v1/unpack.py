#!/usr/bin/env python3
import argparse,base64,hashlib,json,pathlib,zlib

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("out"); a=ap.parse_args(); out=pathlib.Path(a.out)
 if out.exists(): raise SystemExit("destination exists")
 pack=json.loads(pathlib.Path("PACK.json").read_text())
 chunks=[]
 for e in pack["parts"]:
  data=pathlib.Path(e["file"]).read_bytes()
  if len(data)!=e["bytes"] or hashlib.sha256(data).hexdigest()!=e["sha256"]: raise SystemExit("part mismatch "+e["file"])
  chunks.append(data)
 enc=b"".join(chunks)
 if len(enc)!=pack["encoded_bytes"] or hashlib.sha256(enc).hexdigest()!=pack["encoded_sha256"]: raise SystemExit("encoded hash mismatch")
 comp=base64.b64decode(enc,validate=True)
 if hashlib.sha256(comp).hexdigest()!=pack["compressed_sha256"]: raise SystemExit("compressed hash mismatch")
 raw=zlib.decompress(comp)
 if hashlib.sha256(raw).hexdigest()!=pack["decoded_json_sha256"]: raise SystemExit("decoded hash mismatch")
 obj=json.loads(raw)
 if len(obj)!=pack["members"]: raise SystemExit("member count mismatch")
 out.mkdir()
 for rel,e in obj.items():
  pp=pathlib.PurePosixPath(rel)
  if pp.is_absolute() or ".." in pp.parts: raise SystemExit("unsafe path")
  data=base64.b64decode(e["b64"],validate=True)
  if len(data)!=e["bytes"] or hashlib.sha256(data).hexdigest()!=e["sha256"]: raise SystemExit("member mismatch "+rel)
  p=out.joinpath(*pp.parts); p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
 print(json.dumps({"status":"PASS_UNPACK","members":len(obj),"member_bytes":sum(e["bytes"] for e in obj.values())},sort_keys=True))
if __name__=="__main__": main()
