#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent
DEP=RESEARCH/'runtime_native_x11_text_pacing_v1'
EXPECTED={
 'go.mod':'db4cfa3665202def1e3c5ae89a3cc1e3292d8c9a',
 'backend_text.go':'157a240147dfed2f8dfae553e090dbe24db832f2',
 'backend_text_test.go':'9dcc33b9367a0a4b4b8b475308919156ae0c3bb5',
 'cmd/controller/main.go':'565494630e48b3fa95eb89daa8e852f9b7094159',
}
GENERATED_BACKEND_BLOB='a766205e0c75288e3583f45ba2b58b58f7aca951'
OLD='''\t\t\t\tif b.textPacing > 0 {\n\t\t\t\t\ttime.Sleep(b.textPacing)\n\t\t\t\t}\n'''
NEW='''\t\t\t\tif b.textPacing > 0 {\n\t\t\t\t\tdeadline := time.Now().Add(b.textPacing)\n\t\t\t\t\tfor time.Now().Before(deadline) {\n\t\t\t\t\t}\n\t\t\t\t}\n'''

def git_blob(data:bytes)->str:
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
def sha256(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--generated',type=Path,required=True); ap.add_argument('--binary',type=Path,required=True); ap.add_argument('--report',type=Path,required=True); a=ap.parse_args()
    if a.generated.exists(): raise SystemExit('generated directory already exists')
    if a.generated.parent.resolve()!=RESEARCH.resolve(): raise SystemExit('generated directory must be direct research sibling')
    checked={}
    for rel,want in EXPECTED.items():
        p=DEP/rel; data=p.read_bytes(); got=git_blob(data)
        if got!=want: raise SystemExit(f'dependency blob mismatch {rel}: {got} != {want}')
        checked[rel]=got
    a.generated.mkdir()
    (a.generated/'cmd/controller').mkdir(parents=True)
    for rel in ('go.mod','backend_text_test.go','cmd/controller/main.go'):
        dst=a.generated/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(DEP/rel,dst)
    source=(DEP/'backend_text.go').read_text()
    if source.count(OLD)!=1: raise SystemExit('expected exactly one sleep block')
    (a.generated/'backend_text.go').write_text(source.replace(OLD,NEW))
    subprocess.run(['gofmt','-w','backend_text.go','backend_text_test.go','cmd/controller/main.go'],cwd=a.generated,check=True)
    generated_blob=git_blob((a.generated/'backend_text.go').read_bytes())
    if generated_blob!=GENERATED_BACKEND_BLOB: raise SystemExit(f'generated backend mismatch {generated_blob}')
    test=subprocess.run(['go','test','./...'],cwd=a.generated,text=True,capture_output=True)
    if test.returncode!=0: raise SystemExit(test.stdout+'\n'+test.stderr)
    a.binary.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['go','build','-trimpath','-o',str(a.binary),'./cmd/controller'],cwd=a.generated,check=True)
    report={'schema':'agent-interface/native-x11-subms-builder-v1','dependency_blobs':checked,'generated_backend_git_blob':generated_blob,'go_test_exitcode':test.returncode,'go_test_stdout':test.stdout,'go_test_stderr':test.stderr,'binary_sha256':sha256(a.binary),'binary_bytes':a.binary.stat().st_size}
    a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
