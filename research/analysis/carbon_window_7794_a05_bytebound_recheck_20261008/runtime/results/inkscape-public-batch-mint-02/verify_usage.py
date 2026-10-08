import json,hashlib,base64
from pathlib import Path
from usage_projection import project
ROOT=Path(__file__).resolve().parent
def require(v,m):
 if not v:raise ValueError(m)
def verify(check_original=True):
 records=[json.loads(x) for x in (ROOT/'primary-source-records.jsonl').read_text().splitlines()];indices=[x['source_line'] for x in records];require(len(set(indices))==len(indices) and indices==sorted(indices),'record line inventory')
 lines=['{}\n']*max(indices)
 for r in records:lines[r['source_line']-1]=r['raw_line']
 selection=json.loads((ROOT/'usage-selection.json').read_text());expected=json.loads((ROOT/'primary-usage.json').read_text())['windows']
 actual=[project(lines,[s])['windows'][0] for s in selection];require(actual==expected,'usage reconstruction')
 images=[]
 for r in records:
  row=json.loads(r['raw_line']);p=row.get('payload',{})
  if p.get('type')=='custom_tool_call_output' and isinstance(p.get('output'),list):
   for b in p['output']:
    url=b.get('image_url','')
    if b.get('type')=='input_image' and url.startswith('data:') and ';base64,' in url:
     head,data=url.split(';base64,',1);binary=base64.b64decode(data,validate=True);images.append({'source_line':r['source_line'],'sha256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'media_type':head[5:],'detail':b.get('detail')})
 require(images==json.loads((ROOT/'primary-images.json').read_text())['images'],'raw source image reconstruction')
 names=[x['case'] for x in json.loads((ROOT/'schedule.json').read_text())];replyhashes=[json.loads((ROOT.parent/'inkscape-public-batch-mint-01/normal-ordinary/replies/001.json').read_text())['reply']['image_reference']['sha256']]+[json.loads((ROOT/n/'replies'/f'{i:03d}.json').read_text())['reply']['image_reference']['sha256'] for n in names for i in (1,3)]
 require(len(images)==9 and sorted(replyhashes)==sorted(x['sha256'] for x in images),'original reply image multiset')
 source=Path('/mnt/c/Users/junny/.codex/sessions/2026/09/12/rollout-2026-09-12T23-46-37-01a09615-a96c-7b70-8284-e6391b885be5.jsonl')
 if source.exists() and check_original:
  wanted={r['source_line']:r['raw_line'] for r in records};last=max(wanted)
  with source.open() as f:
   for i,line in enumerate(f,1):
    if i in wanted:require(line==wanted[i],'original session line changed')
    if i==last:break
  require(i==last,'original session incomplete')
  sourcecheck='all retained raw lines match original session'
 else:sourcecheck='original session not checked; retained projection and image reconstruction only'
 return {'status':'PASS_USAGE_RECONSTRUCTION','retained_records':len(records),'original_images':len(images),'windows':len(actual),'joint_totals':actual[0]['totals'],'source_check':sourcecheck,'contexts':sorted({str(c.get('context')) for w in actual for c in w['calls']}),'scope':'nested windows overlap; no causal arm savings, model snapshot attestation, per-tool charge or billing amount'}
if __name__=='__main__':
 result=verify();text=json.dumps(result,indent=2);(ROOT/('usage-verify-normal.json' if __debug__ else 'usage-verify-optimized.json')).write_text(text+'\n');print(text)
