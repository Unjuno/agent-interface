"""Execute the preregistered OpenTTD sign-transparency transform through the shared runtime."""
import hashlib,json,subprocess,sys,tempfile,time,shutil,os
from pathlib import Path
from append_checkpoint_v1 import load
from durable_submit_v4 import initialize,run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
HERE=Path(__file__).resolve().parent;ROOT=HERE/'results/openttd-sign-view-paused-01';RUN=ROOT/'run';RUN.mkdir(parents=True,exist_ok=False)
def dump(name,value):
    path=ROOT/name;temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
plan=json.loads((ROOT/'preregistration.json').read_text());assert plan['status']=='PREREGISTERED_BEFORE_EXECUTION' and plan['model_calls']==0
p=subprocess.Popen([sys.executable,'-u',str(HERE/'pointer_socket_entry_v9.py'),'openttd-straight','serve','--','--root','/home/taka/agent-interface-bench-feasibility','--out',str(RUN/'runtime'),'--controller','assistant'],stdout=subprocess.PIPE,stderr=(RUN/'stderr.txt').open('w'),text=True)
temporary=tempfile.TemporaryDirectory(prefix='agent-interface-view-transform-');journal=Path(temporary.name)/'journal.jsonl';calls=[]
try:
    endpoint=json.loads(p.stdout.readline());dump('endpoint.json',endpoint);initial=request_once(endpoint['socket'],start(endpoint['socket']),{'events':['observation'],'timeout':30});dump('initial.json',initial);initialize(journal,initial['continuation'])
    def call(spec):
        result=run(journal,spec);calls.append(result);dump('calls.json',calls);assert result['state']['pending'] is None;return result
    def clock():return call({'command':{'op':'clock'},'timeout':3})['state']['last_resolution']['clock']
    before=initial['continuation']['observation'];current=clock();fresh=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+10_000_000_000,'steps':[{'op':'observe'}]},'timeout':3});current=clock()
    trees=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+10_000_000_000,'steps':[{'op':'chord','modifier':'Control_L','key':'2'},{'op':'observe'}]},'timeout':5});dump('trees-transparent.json',trees);current=clock()
    paused=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+10_000_000_000,'steps':[{'op':'key','key':'F1'},{'op':'observe'}]},'timeout':5});dump('paused.json',paused);current=clock()
    stable=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+10_000_000_000,'steps':[{'op':'observe'}]},'timeout':5});before_sign=stable['state']['continuation']['observation'];dump('stable.json',stable);current=clock()
    applied=call({'command':{'op':'submit','expected_sequence':current['sequence'],'valid_until_ns':current['runtime_ns']+10_000_000_000,'steps':[{'op':'chord','modifier':'Control_L','key':'1'},{'op':'observe'}]},'timeout':5});after_sign=applied['state']['continuation']['observation'];dump('applied.json',applied)
    finish=request_once(endpoint['socket'],applied['state']['continuation'],{'events':['independent_evaluation'],'timeout':25,'command':{'op':'finish'},'request_id':'finish-once'});dump('finish.json',finish);assert p.wait(timeout=10)==0
    evaluation=next(e for e in finish['reply']['records'] if e['event']=='independent_evaluation');before_image=RUN/'runtime'/Path(before_sign['image']).name;after_image=RUN/'runtime'/Path(after_sign['image']).name
    paused_image=RUN/'runtime'/Path(paused['state']['continuation']['observation']['image']).name
    result={'executed':True,'model_calls':0,'precondition_steps':[{'op':'chord','modifier':'Control_L','key':'2'},{'op':'key','key':'F1'}],'step':{'op':'chord','modifier':'Control_L','key':'1'},'paused_image':paused_image.name,'paused_sha256':sha(paused_image),'before_image':before_image.name,'after_image':after_image.name,'before_sha256':sha(before_image),'after_sha256':sha(after_image),'image_changed':sha(before_image)!=sha(after_image),'evaluation':evaluation,'durable_calls':len(calls),'save_unchanged':json.loads((RUN/'runtime/cleanup.json').read_text())['save_unchanged']}
    dump('result.json',result);print(json.dumps(result,indent=2))
finally:
    if journal.exists():shutil.copy2(journal,RUN/'journal.jsonl')
    if p.poll() is None:p.terminate();p.wait(timeout=10)
    temporary.cleanup()
