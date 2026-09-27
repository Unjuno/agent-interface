from __future__ import annotations
import argparse, base64, hashlib, json, time, urllib.request
from datetime import datetime,timezone
from pathlib import Path

MODEL="qwen2.5vl:3b"; DIGEST="fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
def sha(b): return hashlib.sha256(b).hexdigest()
def get_json(url):
    with urllib.request.urlopen(url,timeout=15) as r: return json.loads(r.read())
def main():
    p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['identity','formal'],required=True); p.add_argument('--root',type=Path,required=True); p.add_argument('--out',type=Path,required=True); p.add_argument('--url',default='http://ollama:11434'); a=p.parse_args()
    root=a.root; out=a.out; tags=get_json(a.url+'/api/tags'); model=next((m for m in tags.get('models',[]) if m.get('name')==MODEL),None)
    if not model or model.get('digest')!=DIGEST: raise SystemExit('STOP_MODEL_IDENTITY_MISMATCH')
    if a.mode=='identity':
        ps=get_json(a.url+'/api/ps')
        if ps.get('models'): raise SystemExit('STOP_SERVER_NOT_EMPTY')
        print(json.dumps({'model':MODEL,'digest':DIGEST,'size':model.get('size'),'details':model.get('details'),'capabilities':model.get('capabilities'),'ollama_ps_empty':True})); return
    pre=json.loads((root/'data/PREFORMAL.json').read_text(encoding='utf-8'))
    formal_dir=out/'formal'; formal_dir.mkdir(parents=True,exist_ok=False)
    seen=[]; error=None
    try:
        for c in pre['formal_cases']:
            image=(root/'data'/c['presentation_path']).read_bytes()
            if sha(image)!=c['presentation_sha256']: raise SystemExit('STOP_PRESENTATION_HASH:'+c['case_id'])
            payload={'model':MODEL,'messages':[{'role':'user','content':pre['prompt'],'images':[base64.b64encode(image).decode('ascii')]}],
                     'format':'json','stream':False,'keep_alive':'5m','options':{'temperature':0,'seed':c['seed'],'num_predict':128}}
            reqbytes=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
            start_ns=time.time_ns(); started=datetime.now(timezone.utc).isoformat()
            req=urllib.request.Request(a.url+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
            try:
                with urllib.request.urlopen(req,timeout=180) as r: response=json.loads(r.read())
            except Exception as e:
                error={'case_id':c['case_id'],'type':type(e).__name__,'message':str(e)}; break
            end_ns=time.time_ns(); ended=datetime.now(timezone.utc).isoformat()
            row={'schema':'visual-temporal-570-r7-raw-call-v1','case_id':c['case_id'],'source_case_id':c['source_case_id'],'arm':c['arm'],'seed':c['seed'],
                 'model':MODEL,'expected_digest':DIGEST,'image_sha256':c['presentation_sha256'],'prior_sha256':c['prior_sha256'],'current_sha256':c['current_sha256'],
                 'prompt_sha256':pre['prompt_sha256'],'request':payload,'request_sha256':sha(reqbytes),'started_utc':started,'started_utc_ns':start_ns,
                 'ended_utc':ended,'ended_utc_ns':end_ns,'response':response,'error':None}
            (formal_dir/(c['case_id']+'.json')).write_text(json.dumps(row,indent=2,sort_keys=True)+'\n',encoding='utf-8'); seen.append(c['case_id'])
    finally:
        status={'schema':'visual-temporal-570-r7-run-status-v1','expected_calls':len(pre['formal_cases']),'completed_calls':len(seen),'completed_case_ids':seen,'failure':error,
                'formal_started':bool(seen),'terminal_utc':datetime.now(timezone.utc).isoformat(),'retries':0}
        (out/'RUN_STATUS.json').write_text(json.dumps(status,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(status));
    if error or len(seen)!=len(pre['formal_cases']): raise SystemExit('HOLD_FORMAL_INCOMPLETE')
if __name__=='__main__': main()
