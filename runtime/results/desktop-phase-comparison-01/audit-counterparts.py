import base64,hashlib,json
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parent

def check(ok,why):
 if not ok:raise ValueError(why)
def read(path):return json.loads(path.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 plan=read(ROOT/'construction-public-pair-plan.json')
 for name,digest in plan['source_hashes'].items():check(sha((ROOT/name).read_bytes())==digest,'frozen source '+name)
 cases=['construction-changed-repair-02','construction-public-repair-01','construction-compact-repair-01'];expected_images=[]
 for name in cases:
  case=ROOT/name;allocation=read(case/'allocation.json');cleanup=read(case/'cleanup.json');ev=read(case/'evaluation.json')
  check(cleanup['host_exit']==0 and len(cleanup['children'])==3 and all(type(x['returncode']) is int for x in cleanup['children']),'terminal '+name)
  path=case/('sheet-'+str(allocation['seed'])+'.xlsx');check(sha(path.read_bytes())==ev['workbook_sha256'],'workbook identity')
  book=load_workbook(path,read_only=True,data_only=True);cells={c.coordinate:c.value for row in book.active for c in row if c.value is not None};book.close()
  check(cells==ev['actual_nonempty_cells']=={'A1':317,'A2':529} and ev['success'] is True,'saved/collateral')
  commands=[read(case/'commands'/f'{i:03d}.json')['op'] for i in range(1,8)];check(commands==['observe','public_method','observe','public_method','review_target','dispatch','close'],'exact command sequence')
  old=read(case/'public-method-2/receipt.json');check(old['confirmed_completed_inputs']==[],'old prefix')
  check(old.get('changed_dependency_refused') is True or old['reason']=='dependency_changed','dependency stop')
  repair=read(case/'public-method-4/receipt.json');check(repair['confirmed_completed_inputs']==['enter','save'],'repair prefix')
  if name=='construction-changed-repair-02':inputs=[read(f)['result'] for f in (case/'bridge').glob('compiled-*-execution.json')]
  else:inputs=[read(case/'public-method-4'/f)['result'] for f in ['enter-input.json','save-input.json']]
  inputs.append(read(case/'public/006-raw.json')['result']);check(len(inputs)==3 and sum(r['execution']['program_emissions'] for r in inputs)==26,'input inventory')
  for row in inputs:
   check(row['status']=='completed' and bool(row['execution']['releases']) and all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in row['execution']['releases']),'neutral released input')
  for i in range(1,7):
   shown=read(case/f'replies/{i:03d}.json')['reply'];ref=shown['image_reference'];data=Path(ref['path']).read_bytes()
   check(sha(data)==ref['sha256'] and base64.b64decode(shown['image']['data'])==data,'original selected image')
   expected_images.append(ref['sha256'])
 records=[json.loads(x) for x in (ROOT/'counterpart-source-records.jsonl').read_text().splitlines()];byline={r['source_line']:r['raw_line'] for r in records};usage=read(ROOT/'counterpart-primary-usage.json')
 for w in usage['windows']:
  for row in [w['begin'],w['end'],*w['usage_records']]:check(sha(byline[row['source_line']].encode())==row['source_sha256'],'exact source record')
  seen={r['response_id']:r['usage'] for r in w['usage_records']}
  for field in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']:check(sum(u[field] for u in seen.values())==w['totals'][field],'unique response usage')
  check(w['cost_usd'] is None,'billing unavailable')
 images=read(ROOT/'counterpart-primary-images.json')['images'];delivered=[]
 for line in byline.values():
  payload=json.loads(line).get('payload',{})
  if payload.get('type')=='custom_tool_call_output' and isinstance(payload.get('output'),list):
   for block in payload['output']:
    url=block.get('image_url','')
    if block.get('type')=='input_image' and isinstance(url,str) and ';base64,' in url:
     check(block.get('detail')=='original','original image input');delivered.append(sha(base64.b64decode(url.split(';base64,',1)[1])))
 check(delivered==expected_images==[r['sha256'] for r in images],'18 actual original model images in C/A/B order')
 print('Three saved workflows, neutral releases, frozen public sources, exact two-window usage and18 primary original image blocks verified; performance HOLD.')
if __name__=='__main__':main()
