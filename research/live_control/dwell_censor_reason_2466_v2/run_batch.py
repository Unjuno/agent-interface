import argparse, json, os, pathlib, subprocess, sys, time
FAMILIES=['TK_CALLBACK','WORKER_FILE']
SCENARIOS=['NORMAL','HORIZON_LATE','FOCUS_LOSS','OWNER_DEATH','BOUND_VIOLATION','UNKNOWN_BOUND']
POLICIES=['GENERIC_CENSOR','CAUSE_AWARE']
CASES=[(rep,fam,sc,pol) for rep in range(2) for fam in FAMILIES for sc in SCENARIOS for pol in POLICIES]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--batch',type=int,choices=range(4),required=True); ap.add_argument('--display',required=True); a=ap.parse_args()
 out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False)
 start_i=a.batch*12; subset=list(enumerate(CASES[start_i:start_i+12],start_i))
 xvfb=subprocess.Popen(['Xvfb',a.display,'-screen','0','640x360x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 env=dict(os.environ); env['DISPLAY']=a.display; time.sleep(.2); rows=[]; t0=time.monotonic_ns()
 try:
  for idx,(rep,family,scenario,policy) in subset:
   case=out/f'case-{idx:03d}-{family}-{scenario}-{policy}-r{rep}'
   cp=subprocess.run([sys.executable,'-B',str(pathlib.Path(__file__).with_name('case_worker.py')),'--family',family,'--scenario',scenario,'--policy',policy,'--rep',str(rep),'--out',str(case)],env=env,text=True,capture_output=True,timeout=3)
   (case/'stdout.txt').write_text(cp.stdout,encoding='utf-8'); (case/'stderr.txt').write_text(cp.stderr,encoding='utf-8'); (case/'exit.json').write_text(json.dumps({'returncode':cp.returncode})+'\n')
   if cp.returncode!=0: raise RuntimeError(f'case {idx} rc={cp.returncode}: {cp.stderr}')
   r=json.loads((case/'result.json').read_text()); r['case_index']=idx; rows.append(r)
  (out/'ROWS.json').write_text(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n')
  (out/'END.json').write_text(json.dumps({'status':'COMPLETE','batch':a.batch,'start_index':start_i,'cases':len(rows),'elapsed_ms':(time.monotonic_ns()-t0)/1e6},sort_keys=True)+'\n')
 finally:
  xvfb.terminate()
  try: xvfb.wait(timeout=2)
  except subprocess.TimeoutExpired: xvfb.kill(); xvfb.wait()
  (out/'xvfb_exit.json').write_text(json.dumps({'returncode':xvfb.returncode})+'\n')
 print(json.dumps({'batch':a.batch,'cases':len(rows),'xvfb_returncode':xvfb.returncode},sort_keys=True))
if __name__=='__main__': main()
