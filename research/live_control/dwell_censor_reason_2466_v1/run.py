import argparse, json, os, pathlib, subprocess, sys, time
FAMILIES=['TK_CALLBACK','WORKER_FILE']
SCENARIOS=['NORMAL','HORIZON_LATE','FOCUS_LOSS','OWNER_DEATH','BOUND_VIOLATION','UNKNOWN_BOUND']
POLICIES=['GENERIC_CENSOR','CAUSE_AWARE']

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--display',default=':97'); a=ap.parse_args()
 out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=False)
 xvfb=subprocess.Popen(['Xvfb',a.display,'-screen','0','640x360x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 env=dict(os.environ); env['DISPLAY']=a.display
 time.sleep(.25)
 rows=[]; start=time.monotonic_ns()
 try:
  idx=0
  for rep in range(2):
   for family in FAMILIES:
    for scenario in SCENARIOS:
     for policy in POLICIES:
      case=out/f'case-{idx:03d}-{family}-{scenario}-{policy}-r{rep}'
      cp=subprocess.run([sys.executable,'-B',str(pathlib.Path(__file__).with_name('case_worker.py')),'--family',family,'--scenario',scenario,'--policy',policy,'--rep',str(rep),'--out',str(case)],env=env,text=True,capture_output=True,timeout=4)
      (case/'stdout.txt').write_text(cp.stdout,encoding='utf-8'); (case/'stderr.txt').write_text(cp.stderr,encoding='utf-8'); (case/'exit.json').write_text(json.dumps({'returncode':cp.returncode})+'\n',encoding='utf-8')
      if cp.returncode!=0: raise RuntimeError(f'case {idx} rc={cp.returncode}: {cp.stderr}')
      row=json.loads((case/'result.json').read_text()); row['case_index']=idx; rows.append(row); idx+=1
  (out/'ROWS.json').write_text(json.dumps(rows,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
  end={'status':'COMPLETE','cases':len(rows),'elapsed_ms':(time.monotonic_ns()-start)/1e6}
  (out/'END.json').write_text(json.dumps(end,sort_keys=True)+'\n',encoding='utf-8')
 finally:
  xvfb.terminate()
  try: xvfb.wait(timeout=2)
  except subprocess.TimeoutExpired: xvfb.kill(); xvfb.wait()
  (out/'xvfb_exit.json').write_text(json.dumps({'returncode':xvfb.returncode})+'\n',encoding='utf-8')
 print(json.dumps({'cases':len(rows),'xvfb_returncode':xvfb.returncode},sort_keys=True))
if __name__=='__main__': main()
