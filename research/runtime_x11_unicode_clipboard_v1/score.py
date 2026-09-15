#!/usr/bin/env python3
import argparse,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
CORPUS=['café','βeta','東京','あいうえお','🙂','e\u0301','naïve','résumé','中文','한국']
def score_writer(p):
    with zipfile.ZipFile(p) as z:r=ET.fromstring(z.read('content.xml'))
    ns='{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
    ps=[''.join(x.itertext()) for x in r.iter(ns+'p')]
    return {'actual':ps[:1+len(CORPUS)],'expected':['sentinel']+CORPUS,'exact':ps[:1+len(CORPUS)]==['sentinel']+CORPUS}
def score_calc(p):
    import openpyxl
    wb=openpyxl.load_workbook(p,data_only=False);ws=wb.active; actual=[ws.cell(i+1,1).value for i in range(len(CORPUS))]
    return {'actual':actual,'expected':CORPUS,'exact':actual==CORPUS}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--app',choices=['writer','calc'],required=True);ap.add_argument('--artifact',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=score_writer(a.artifact) if a.app=='writer' else score_calc(a.artifact);r['app']=a.app;a.out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2));return 0 if r['exact'] else 1
if __name__=='__main__':raise SystemExit(main())
