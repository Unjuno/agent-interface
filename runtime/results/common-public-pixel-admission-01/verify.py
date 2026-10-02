import base64,hashlib,json
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parent
def require(ok,message):
    if not ok:raise ValueError(message)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    archive=sha(ROOT/'runtime.pyz')
    require(archive=='35dca1af92c7e91bdd81cf470bdc7c97264049f1b0d95a525ccfe0609d873eeb','frozen archive')
    for route,seed in [('plain',1002087),('compact',1002088)]:
        case=ROOT/route; allocation=read(case/'allocation.json')
        require(allocation['seed']==seed and allocation['archive_sha256']==archive and allocation['retry_budget']==0,'allocation identity')
        cleanup=read(case/'cleanup.json');evaluation=read(case/'evaluation.json')
        require(cleanup['host_exit']==0 and len(cleanup['children'])==3 and all(type(x['returncode']) is int for x in cleanup['children']),'terminal owned children')
        require(evaluation['after_all_owned_processes_terminal'] is True and evaluation['success'] is True,'post-terminal evaluation')
        workbook=case/f'sheet-{seed}.xlsx'
        require(sha(workbook)==evaluation['workbook_sha256'],'saved workbook hash')
        book=load_workbook(workbook,read_only=True,data_only=True)
        actual={cell.coordinate:cell.value for row in book.active for cell in row if cell.value is not None};book.close()
        require(actual=={'A1':317,'A2':529}==evaluation['actual_nonempty_cells'],'independent cells')
        replies=[read(case/'replies'/f'{i:03d}.json') for i in range(1,8)]
        require([r['request']['op'] for r in replies]==['observe','dispatch','read_cells','dispatch','review_target','dispatch','close'],'original command order')
        require(len(list((case/'commands').glob('*.json')))==7,'no extra command')
        for i in range(1,8):
            require(read(case/'commands'/f'{i:03d}.json')==replies[i-1]['request'],'original request matches reply')
            r=replies[i-1];raw=read(case/'public'/f'{i:03d}-raw.json')
            require(r['started_ns']<=r['ended_ns']<=cleanup['ended_ns'],'terminal chronology')
            ref=r['reply'].get('image_reference',{})
            if r['reply'].get('image_status')=='image':
                artifact=case/'public/images'/Path(ref['path']).name
                require(sha(artifact)==ref['sha256'],'native PNG identity')
                require(base64.b64decode(r['reply']['image']['data'])==artifact.read_bytes(),'original public embedded PNG')
            if i in [2,4,6]:
                execution=raw['result']['execution']
                require(execution['program_emissions']=={2:20,4:4,6:2}[i],'incremental emissions')
                require(execution['emissions']=={2:20,4:24,6:26}[i],'cumulative emissions')
                require(raw['result']['status']=='completed' and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in execution['releases']),'verified input release')
        readback=read(case/'public/003-raw.json')
        require(readback['source_sha256']==replies[1]['reply']['image_reference']['sha256'],'callback reads delivered image')
        require([readback['reading'][k]['value'] for k in ['A1','A2','B1']]==['317','529',None],'unchanged readings including unknown')
        close=read(case/'public/007-raw.json')
        require(close['status']=='closed' and close['release']['verified'] and close['connection_close_attempted'],'original owner close')
        if route=='plain':
            require(replies[5]['reply']['image_status']=='no_observation' and replies[5]['reply']['image'] is None,'withheld inconsistent image')
            require(read(case/'public/006-raw.json')['post_dispatch_inspection']['error']=='TARGET_CHANGED_DURING_CAPTURE','retained capture failure')
        print(route+': original evidence verified; saved 317/529; no comparison promotion')
def verify_accounting():
    records=[json.loads(line) for line in (ROOT/'source-records.jsonl').read_text().splitlines()]
    byline={r['source_line']:r['raw_line'] for r in records}
    projection=read(ROOT/'primary-usage.json');window=projection['windows'][0]
    for row in window['usage_records']+[window['begin'],window['end']]:
        require(hashlib.sha256(byline[row['source_line']].encode()).hexdigest()==row['source_sha256'],'exact source usage/boundary identity')
    seen={}
    for row in window['usage_records']:seen[row['response_id']]=row['usage']
    require(all(sum(v[k] for v in seen.values())==window['totals'][k] for k in ['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']),'deduplicated actual usage totals')
    delivered=[]
    for raw in byline.values():
        p=json.loads(raw).get('payload',{})
        if p.get('type')=='custom_tool_call_output' and isinstance(p.get('output'),list):
            for b in p['output']:
                url=b.get('image_url','')
                if b.get('type')=='input_image' and isinstance(url,str) and url.startswith('data:image/png;base64,'):
                    require(b.get('detail')=='original','original image detail')
                    delivered.append(hashlib.sha256(base64.b64decode(url.split(',',1)[1])).hexdigest())
    images=read(ROOT/'primary-image-audit.json')['images']
    require(len(delivered)==9 and delivered==[x['sha256'] for x in images],'actual original image inputs')
    expected=[]
    for route,ids in [('plain',[1,2,4,5]),('compact',[1,2,4,5,6])]:
        expected.extend(read(ROOT/route/'replies'/f'{i:03d}.json')['reply']['image_reference']['sha256'] for i in ids)
    require(delivered==expected,'model PNG inputs match original public artifacts')
    print('Joint actual usage and nine original PNG inputs verified; billing unavailable.')
if __name__=='__main__':main();verify_accounting()
