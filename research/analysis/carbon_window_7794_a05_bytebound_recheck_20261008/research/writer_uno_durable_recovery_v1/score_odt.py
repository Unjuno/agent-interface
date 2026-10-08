#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
TEXT_NS='{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
def text_of(path:Path):
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        raw=z.read('content.xml')
        root=ET.fromstring(raw)
        parts=[]
        for p in root.iter(TEXT_NS+'p'):
            parts.append(''.join(p.itertext()))
        return '\n'.join(parts),bad,hashlib.sha256(path.read_bytes()).hexdigest(),len(path.read_bytes())
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--a',type=Path,required=True);ap.add_argument('--b',type=Path,required=True);ap.add_argument('--expect-a',required=True);ap.add_argument('--expect-b',required=True);ap.add_argument('--out',type=Path,required=True);x=ap.parse_args()
    ta,ba,ha,sa=text_of(x.a);tb,bb,hb,sb=text_of(x.b)
    o={'a':{'text':ta,'zip_bad':ba,'sha256':ha,'bytes':sa},'b':{'text':tb,'zip_bad':bb,'sha256':hb,'bytes':sb}}
    o['passed']=ta==x.expect_a and tb==x.expect_b and ba is None and bb is None
    x.out.write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n');print(json.dumps(o,ensure_ascii=False));return 0 if o['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
