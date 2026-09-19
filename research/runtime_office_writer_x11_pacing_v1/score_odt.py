#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from odf.opendocument import load
from odf.text import P
from odf import teletype
CORPUS=['office','coffee','bookkeeper','committee','parallel','address','success','letterpress','mississippi','assessment','committee','bookkeeping','ffffffffff','aaaaaaaaaa','tttttttttt','ssssssssss']
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--odt',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); doc=load(str(a.odt)); paras=[teletype.extractText(p) for p in doc.getElementsByType(P)]; observed=paras[1:1+len(CORPUS)]; mism=[{'row':i+1,'expected':e,'observed':observed[i] if i<len(observed) else None} for i,e in enumerate(CORPUS) if i>=len(observed) or observed[i]!=e]; out={'schema':'agent-interface/writer-x11-pacing-score-v1','passed':not mism and len(observed)==len(CORPUS),'sentinel':paras[0] if paras else None,'expected':CORPUS,'observed':observed,'mismatches':mism,'odt_sha256':hashlib.sha256(a.odt.read_bytes()).hexdigest(),'odt_bytes':a.odt.stat().st_size}; a.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2)); return 0 if out['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
