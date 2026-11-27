import pathlib,sys,subprocess,datetime,hashlib,json,os
p=pathlib.Path(__file__).resolve().parent
def h(b):return hashlib.sha256(b).hexdigest()
files=[x for x in p.iterdir() if x.is_file()]
(p/'PRE_RUN_MANIFEST.json').write_text(json.dumps({x.name:{'bytes':x.stat().st_size,'sha256':h(x.read_bytes())} for x in files},indent=2),encoding='utf-8')
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
argv=[sys.executable,'-X','utf8','-B',str(p/'actor.py')]
child=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=p)
timeout=False
try:out,err=child.communicate(timeout=30)
except subprocess.TimeoutExpired:
 timeout=True;child.kill();out,err=child.communicate()
end=datetime.datetime.now(datetime.timezone.utc).isoformat()
(p/'stdout.txt').write_bytes(out);(p/'stderr.txt').write_bytes(err)
receipt={'argv':argv,'cwd':str(p),'supervisor_pid':os.getpid(),'actor_pid':child.pid,'start_utc':start,'end_utc':end,'exit_code':child.returncode,'timeout':timeout,'stdout':{'bytes':len(out),'sha256':h(out)},'stderr':{'bytes':len(err),'sha256':h(err)}}
(p/'RUN_RECEIPT.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt));print(err.decode('utf-8'))
sys.exit(child.returncode)
