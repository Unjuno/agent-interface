"""Fresh one-shot stale-source MCP control; handles compact receipts safely."""
import asyncio,base64,hashlib,json,os
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(os.environ.get('STALE_EVIDENCE_DIR','/evidence/stale_source_v2'))

def persist(name,result):
 payload=result.model_dump(mode='json'); (ROOT/name).write_text(json.dumps(payload,sort_keys=True)+'\n')
 images=[]
 for i,b in enumerate(result.content):
  if b.type=='image':
   data=base64.b64decode(b.data,validate=True); path=ROOT/f'{name.removesuffix(".json")}-image-{i}.png'
   path.write_bytes(data); images.append({'path':path.name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 return payload,images

def meta(payload):
 if payload.get('isError'):
  return {'status':'mcp_error','text':[x.get('text','') for x in payload.get('content',[])]}
 for b in payload.get('content',[]):
  if b.get('type')=='text':
   try: return json.loads(b['text'])
   except (ValueError,TypeError): return {'status':'non_json','text':b.get('text','')}
 return {'status':'no_text'}

def native_status(m):
 return m.get('receipt',{}).get('native_result',{}).get('status',m.get('status'))

async def main():
 ROOT.mkdir(parents=True,exist_ok=True)
 params=StdioServerParameters(command='/opt/mcp/bin/python',cwd='/workspace',args=[
  '/workspace/research/live_control/native_mcp_v1.py','--allocation-directory',str(ROOT/'allocation'),
  '--app','inkscape','--seed','991123','--max-stages','3','--harness-python','/usr/bin/python3'],
  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':'/workspace:/workspace/research/live_control',
       'HOME':'/tmp/3370-stale-source-v2-home'})
 Path('/tmp/3370-stale-source-v2-home').mkdir(exist_ok=True)
 with (ROOT/'mcp-stderr.log').open('w') as err:
  async with stdio_client(params,errlog=err) as (reader,writer):
   async with ClientSession(reader,writer) as client:
    await client.initialize(); tools=await client.list_tools()
    (ROOT/'tools.json').write_text(json.dumps(sorted(t.name for t in tools.tools))+'\n')
    start=await client.call_tool('native_start',{'timeout':30}); sp,si=persist('start.json',start)
    sm=meta(sp); (ROOT/'start-meta.json').write_text(json.dumps(sm,indent=2,sort_keys=True)+'\n')
    if start.isError or len(si)!=1 or sm.get('image_reference',{}).get('sequence')!=1:
     (ROOT/'client-result.json').write_text(json.dumps({'disposition':'STOP_START','start':sm},indent=2)+'\n'); return
    (ROOT/'start-images.json').write_text(json.dumps(si,indent=2,sort_keys=True)+'\n')
    obs=await client.call_tool('native_submit',{'stage':1,'decision':{'source_sequence':1,'interaction':'observe'},'timeout':10})
    op,oi=persist('observe.json',obs); om=meta(op)
    (ROOT/'observe-meta.json').write_text(json.dumps(om,indent=2,sort_keys=True)+'\n')
    (ROOT/'observe-images.json').write_text(json.dumps(oi,indent=2,sort_keys=True)+'\n')
    nr=om.get('receipt',{}).get('native_result',{})
    if obs.isError or native_status(om)!='boundary' or nr.get('observation',{}).get('sequence')!=2:
     (ROOT/'client-result.json').write_text(json.dumps({'disposition':'STOP_OBSERVE_RESPONSE_SHAPE','observe':om},indent=2)+'\n'); return
    stale=await client.call_tool('native_submit',{'stage':2,'decision':{
     'source_sequence':1,'point':[600,389],'expected_title':'Inkscape','interaction':'click',
     'tail':[{'op':'key_chord','keys':['Right'],'repeat':18}],'finish_after':True},'timeout':2})
    tp,_=persist('stale-submit.json',stale); tm=meta(tp)
    (ROOT/'stale-submit-meta.json').write_text(json.dumps(tm,indent=2,sort_keys=True)+'\n')
    if not stale.isError or 'decision must name the presented source' not in str(tm):
     (ROOT/'client-result.json').write_text(json.dumps({'disposition':'FAIL_STALE_NOT_REFUSED',
      'stale_meta':tm},indent=2)+'\n'); return
    # Close the still-waiting owner only through a current-source read-only
    # observation followed by an explicit no-input finish; never replay action.
    fresh=await client.call_tool('native_submit',{'stage':2,'decision':{
     'source_sequence':2,'interaction':'observe'},'timeout':10})
    fp,fi=persist('fresh-observe.json',fresh); fm=meta(fp)
    (ROOT/'fresh-observe-meta.json').write_text(json.dumps(fm,indent=2,sort_keys=True)+'\n')
    fr=fm.get('receipt',{}).get('native_result',{})
    if fresh.isError or native_status(fm)!='boundary' or fr.get('observation',{}).get('sequence')!=3:
     (ROOT/'client-result.json').write_text(json.dumps({'disposition':'STOP_CLEANUP_OBSERVE',
      'stale_meta':tm,'fresh_meta':fm},indent=2)+'\n'); return
    finish=await client.call_tool('native_submit',{'stage':3,'decision':{
     'source_sequence':3,'finish':True},'timeout':10})
    xp,_=persist('finish.json',finish); xm=meta(xp)
    (ROOT/'finish-meta.json').write_text(json.dumps(xm,indent=2,sort_keys=True)+'\n')
    polls=[]; final={}
    for _ in range(40):
     status=await client.call_tool('native_status',{}); pp,_=persist('status.json',status); final=meta(pp)
     state=final.get('allocation',{}).get('status'); polls.append(state)
     if state in ('terminal','needs_review'): break
     await asyncio.sleep(.1)
    result={'disposition':'CONTROL_CAPTURED','observe_status':native_status(om),
     'source1_sequence':sm.get('image_reference',{}).get('sequence'),
     'source2_sequence':nr.get('observation',{}).get('sequence'),'stale_is_error':stale.isError,
     'stale_meta':tm,'cleanup_observation_sequence':fr.get('observation',{}).get('sequence'),
     'finish_is_error':finish.isError,'finish_status':native_status(xm),
     'status_polls':polls,'final_status':final}
    (ROOT/'client-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'event':'STALE_SOURCE_CONTROL_DONE',**result},sort_keys=True),flush=True)
asyncio.run(main())
