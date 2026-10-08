import base64,hashlib,json
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parent

def require(ok,reason):
    if not ok:raise ValueError(reason)
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    identity=read(ROOT/'caller-identities.json')
    for name,digest in identity.items():require(sha(ROOT/name)==digest,'frozen source changed '+name)
    require(sha(ROOT/'runtime.pyz')=='39319f781ef0fc79a5e357271d2c6befd70f71a227c5b8a5a9021b2ddcab8a8d','archive')
    case=ROOT/'plain';method=case/'public-method-2'
    allocation=read(case/'allocation.json');require(allocation['seed']==1002089 and allocation['retry_budget']==0,'original allocation')
    cleanup=read(case/'cleanup.json');require(cleanup['host_exit']==0 and len(cleanup['children'])==3 and all(type(r['returncode']) is int for r in cleanup['children']),'all children terminal')
    evaluation=read(case/'evaluation.json');require(evaluation['success'] is False and evaluation['after_all_owned_processes_terminal'] is True and evaluation['actual_nonempty_cells']=={},'retained task failure')
    workbook=case/'sheet-1002089.xlsx';require(sha(workbook)==evaluation['workbook_sha256'],'workbook bytes')
    book=load_workbook(workbook,read_only=True,data_only=True);actual={c.coordinate:c.value for row in book.active for c in row if c.value is not None};book.close();require(actual=={},'independent saved values')
    replies=[read(case/'replies'/f'{i:03d}.json') for i in range(1,4)]
    require([r['request']['op'] for r in replies]==['observe','public_method','close'],'no extra input or confirmation')
    require(len(list((case/'commands').glob('*.json')))==3,'actual command inventory')
    for name,count in [('enter',20),('save',4)]:
        raw=read(method/(name+'-input.json'));e=raw['result']['execution']
        require(raw['result']['status']=='completed' and e['program_emissions']==count,'original completed input')
        require(bool(e['releases']) and all(r['verified'] and r['keys_down']==[] and r['buttons_down']==[] for r in e['releases']),'verified neutral release')
    prefix=read(method/'receipt.json');require(prefix['confirmed_completed_inputs']==['enter','save'] and prefix['task_success'] is None and prefix['replay_allowed'] is False,'mechanics not persisted success')
    require([read(method/f'perception-{n}.json')['reading'][k]['value'] for n in [1,2] for k in ['A1','A2']]==[None,None,'317','529'],'original pixel readings')
    shown=replies[1]['reply'];require(shown['image'] is None and shown['image_status']=='needs_review' and shown['image_error']=='image outside run directory','actual wrapper failure')
    first=replies[0]['reply'];ref=first['image_reference'];artifact=case/'public/images'/Path(ref['path']).name
    require(sha(artifact)==ref['sha256'] and base64.b64decode(first['image']['data'])==artifact.read_bytes(),'original delivered initial PNG')
    close=read(case/'public/003-raw.json');require(close['status']=='closed' and close['release']['verified'] and close['connection_close_attempted'],'closed original owner')
    print('Original mechanics/prefix/release and independently failed saved task verified.')
    if (ROOT/'primary-usage.json').exists():
        records=[json.loads(x) for x in (ROOT/'source-records.jsonl').read_text().splitlines()];byline={r['source_line']:r['raw_line'] for r in records};w=read(ROOT/'primary-usage.json')['windows'][0]
        for row in [w['begin'],w['end'],*w['usage_records']]:require(hashlib.sha256(byline[row['source_line']].encode()).hexdigest()==row['source_sha256'],'exact usage source')
        seen={r['response_id']:r['usage'] for r in w['usage_records']}
        for field in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']:require(sum(v[field] for v in seen.values())==w['totals'][field],'actual unique usage')
        images=read(ROOT/'primary-image-audit.json')['images'];require(len(images)==1 and images[0]['detail']=='original' and images[0]['sha256']==ref['sha256'],'one actual original primary image')
        delivered=[]
        for line in byline.values():
            payload=json.loads(line).get('payload',{})
            if payload.get('type')=='custom_tool_call_output' and isinstance(payload.get('output'),list):
                for block in payload['output']:
                    url=block.get('image_url','')
                    if block.get('type')=='input_image' and isinstance(url,str) and url.startswith('data:image/png;base64,'):
                        require(block.get('detail')=='original','original model PNG detail')
                        delivered.append(hashlib.sha256(base64.b64decode(url.split(',',1)[1])).hexdigest())
        require(delivered==[ref['sha256']],'actual model PNG bytes match original source')
        print('Joint source usage verified; one original primary PNG; billing unavailable.')
if __name__=='__main__':main()
