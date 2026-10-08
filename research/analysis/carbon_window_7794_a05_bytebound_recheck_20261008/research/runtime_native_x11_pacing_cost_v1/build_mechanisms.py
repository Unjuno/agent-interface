#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent
DEP=RESEARCH/'runtime_native_x11_text_pacing_v1'
CORE=RESEARCH/'runtime_native_core_v0'
EXPECTED={
 'go.mod':'db4cfa3665202def1e3c5ae89a3cc1e3292d8c9a',
 'backend_text.go':'157a240147dfed2f8dfae553e090dbe24db832f2',
 'backend_text_test.go':'9dcc33b9367a0a4b4b8b475308919156ae0c3bb5',
 'cmd/controller/main.go':'565494630e48b3fa95eb89daa8e852f9b7094159',
}

def git_blob(data:bytes)->str:
 return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
def sha256(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
BUSY='''\t\t\t\tif b.textPacing > 0 {\n\t\t\t\t\tdeadline := time.Now().Add(b.textPacing)\n\t\t\t\t\tfor time.Now().Before(deadline) {\n\t\t\t\t\t}\n\t\t\t\t}\n'''
SLEEP='''\t\t\t\tif b.textPacing > 0 {\n\t\t\t\t\ttime.Sleep(b.textPacing)\n\t\t\t\t}\n'''
HYBRID='''\t\t\t\tif b.textPacing > 0 {\n\t\t\t\t\tdeadline := time.Now().Add(b.textPacing)\n\t\t\t\t\ttail := 200 * time.Microsecond\n\t\t\t\t\tif b.textPacing > tail {\n\t\t\t\t\t\ttime.Sleep(b.textPacing - tail)\n\t\t\t\t\t}\n\t\t\t\t\tfor time.Now().Before(deadline) {\n\t\t\t\t\t}\n\t\t\t\t}\n'''

def instrument_controller(text:str)->str:
 text=text.replace('"sort"\n\t"time"','"sort"\n\t"syscall"\n\t"time"')
 marker='func median(v []int64) int64 {\n'
 helper='''func processCPUNS() int64 {\n\tvar r syscall.Rusage\n\tif err := syscall.Getrusage(syscall.RUSAGE_SELF, &r); err != nil { return -1 }\n\treturn int64(r.Utime.Sec)*1_000_000_000 + int64(r.Utime.Usec)*1_000 + int64(r.Stime.Sec)*1_000_000_000 + int64(r.Stime.Usec)*1_000\n}\n\n'''
 if marker not in text: raise RuntimeError('median marker missing')
 text=text.replace(marker,helper+marker,1)
 old='''\tt0 := time.Now()\n\ttr := b.Execute(task, 5, 1)\n\teditNS := time.Since(t0).Nanoseconds()\n'''
 new='''\tcpu0 := processCPUNS()\n\tt0 := time.Now()\n\ttr := b.Execute(task, 5, 1)\n\teditNS := time.Since(t0).Nanoseconds()\n\tcpu1 := processCPUNS()\n\teditCPUNS := cpu1 - cpu0\n'''
 if old not in text: raise RuntimeError('edit marker missing')
 text=text.replace(old,new,1)
 old2='''"edit_elapsed_ns": editNS, "median_char_call_ns": median(tr.TextCharDurationsNS),'''
 new2='''"edit_elapsed_ns": editNS, "edit_process_cpu_ns": editCPUNS, "median_char_call_ns": median(tr.TextCharDurationsNS),'''
 if old2 not in text: raise RuntimeError('result marker missing')
 return text.replace(old2,new2,1)

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 if a.out.exists():raise SystemExit('output exists')
 rows={}
 for rel,want in EXPECTED.items():
  p=DEP/rel; got=git_blob(p.read_bytes())
  if got!=want:raise SystemExit(f'dependency blob mismatch {rel}: {got} != {want}')
 base_backend=(DEP/'backend_text.go').read_text()
 if base_backend.count(SLEEP)!=1:raise SystemExit('sleep pacing block mismatch')
 controller=instrument_controller((DEP/'cmd/controller/main.go').read_text())
 a.out.mkdir(parents=True)
 shutil.copytree(CORE,a.out/'runtime_native_core_v0')
 mechanisms={'sleep':SLEEP,'busy':BUSY,'hybrid200':HYBRID}
 for name,block in mechanisms.items():
  d=a.out/name;d.mkdir()
  shutil.copy2(DEP/'go.mod',d/'go.mod');shutil.copy2(DEP/'backend_text_test.go',d/'backend_text_test.go')
  backend=base_backend.replace(SLEEP,block,1);(d/'backend_text.go').write_text(backend)
  (d/'cmd/controller').mkdir(parents=True);(d/'cmd/controller/main.go').write_text(controller)
  test=subprocess.run(['go','test','./...'],cwd=d,text=True,capture_output=True)
  (d/'go-test.stdout').write_text(test.stdout);(d/'go-test.stderr').write_text(test.stderr)
  if test.returncode:raise SystemExit(f'{name} go test failed')
  binary=a.out/f'{name}-controller'
  build=subprocess.run(['go','build','-o',str(binary),'./cmd/controller'],cwd=d,text=True,capture_output=True)
  if build.returncode:raise SystemExit(f'{name} build failed: {build.stderr}')
  rows[name]={'backend_git_blob':git_blob((d/'backend_text.go').read_bytes()),'controller_git_blob':git_blob((d/'cmd/controller/main.go').read_bytes()),'binary_sha256':sha256(binary),'binary_bytes':binary.stat().st_size,'go_test_exit':test.returncode}
 report={'schema':'agent-interface/native-x11-pacing-cost-build-v1','dependency_blobs':EXPECTED,'mechanisms':rows}
 (a.out/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
