import subprocess,sys
report,events,guard,candidate,auditor,out=sys.argv[1:]
commands=[[sys.executable,'-B',candidate,report,events,guard,out+'/candidate.json'],[sys.executable,'-B',auditor,report,events,out+'/candidate.json',out+'/audit.json']]
for i,cmd in enumerate(commands):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
 open(out+f'/stage-{i+1}.stdout.txt','w',encoding='utf-8').write(p.stdout)
 open(out+f'/stage-{i+1}.stderr.txt','w',encoding='utf-8').write(p.stderr)
 if p.returncode: print(f'stage_{i+1}_exit={p.returncode}'); print(p.stderr); raise SystemExit(p.returncode)
print('candidate_and_independent_audit=PASS')
