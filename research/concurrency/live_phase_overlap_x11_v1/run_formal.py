import json, os, pathlib, subprocess, sys, time, statistics

root=pathlib.Path(__file__).parent
schedule=json.loads((root/'schedule.json').read_text())
raw=[]
for idx,row in enumerate(schedule['cases']):
    disp=220+idx
    xauth=root/f'.xauth-{idx}'
    xauth.write_bytes(b'')
    env=os.environ.copy(); env['DISPLAY']=f':{disp}'; env['XAUTHORITY']=str(xauth)
    xvfb=subprocess.Popen(['Xvfb',f':{disp}','-screen','0','800x600x24','-nolisten','tcp'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,text=True)
    ready=False
    try:
        for _ in range(100):
            p=subprocess.run(['xdpyinfo'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            if p.returncode==0:
                ready=True; break
            time.sleep(0.01)
        if not ready:
            raw.append({'case_id':row['case_id'],'arm':row['arm'],'setup_error':'Xvfb not ready'}); continue
        p=subprocess.run([sys.executable,str(root/'run_case.py'),'--arm',row['arm'],'--delay-ms','150'],env=env,capture_output=True,text=True,timeout=5)
        if p.returncode!=0:
            raw.append({'case_id':row['case_id'],'arm':row['arm'],'returncode':p.returncode,'stderr':p.stderr,'stdout':p.stdout}); continue
        result=json.loads(p.stdout.strip().splitlines()[-1])
        result['case_id']=row['case_id']; result['schedule_index']=idx
        raw.append(result)
    finally:
        xvfb.terminate()
        try: xvfb.wait(timeout=2)
        except subprocess.TimeoutExpired:
            xvfb.kill(); xvfb.wait()
        xauth.unlink(missing_ok=True)

(root/'RAW_CASES.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
by_arm={}
for r in raw:
    by_arm.setdefault(r['arm'],[]).append(r)
summary={}
for arm,rows in by_arm.items():
    if rows and all('wall_ms' in r for r in rows):
        summary[arm]={
            'n':len(rows),
            'median_wall_ms':statistics.median(r['wall_ms'] for r in rows),
            'pixel_correct_n':sum(bool(r['pixel_correct']) for r in rows),
            'space_neutral_n':sum(bool(r['space_neutral']) for r in rows),
        }
serial=summary.get('serial_independent',{}).get('median_wall_ms')
overlap=summary.get('overlap_independent',{}).get('median_wall_ms')
metrics={
    'serial_independent_median_wall_ms':serial,
    'overlap_independent_median_wall_ms':overlap,
    'median_reduction_ms': None if serial is None or overlap is None else serial-overlap,
    'overlap_serial_ratio': None if serial is None or overlap is None else overlap/serial,
}
out={'formal_invocations':1,'reruns':0,'tuning_after_freeze':0,'case_count':len(raw),'summary':summary,'metrics':metrics}
(root/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
