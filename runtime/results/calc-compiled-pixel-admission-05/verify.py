import base64,hashlib,json
from pathlib import Path
from openpyxl import load_workbook
ROOT=Path(__file__).resolve().parent

def require(condition,message):
    if not condition: raise ValueError(message)

def main():
    usage=json.loads((ROOT/'usage.json').read_text())['windows'][0]
    records={row['source_line']:row for row in map(json.loads,(ROOT/'exact-source-records.jsonl').read_text().splitlines())}
    usage_ids={}
    images=[]
    for row in records.values():
        record=json.loads(row['raw_line']);payload=record.get('payload',{})
        if record.get('type')=='token_usage_record':
            rid=payload['response_id'];values=payload['usage']
            if rid in usage_ids: require(values==usage_ids[rid],'conflicting usage identity')
            usage_ids[rid]=values
        if payload.get('type')=='custom_tool_call_output' and type(payload.get('output')) is list:
            for item in payload['output']:
                if item.get('type')=='input_image':
                    url=item['image_url'];require(url.startswith('data:image/png;base64,'),'unexpected model image encoding')
                    data=base64.b64decode(url.split(',',1)[1],validate=True)
                    images.append({'source_line':row['source_line'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'detail':item.get('detail')})
    stamps=[usage['begin'],usage['end'],*usage['usage_records']]
    for call in usage['calls']:
        stamps.append(call)
        if 'output' in call:stamps.append(call['output'])
    for stamp in stamps:
        require(hashlib.sha256(records[stamp['source_line']]['raw_line'].encode()).hexdigest()==stamp['source_sha256'],'source stamp mismatch')
    for field in ('input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens','cache_write_input_tokens'):
        require(sum(x[field] for x in usage_ids.values())==usage['totals'][field],'usage total mismatch '+field)
    require(len(images)==2,'actual model image count mismatch')
    expected=[]
    for n in ('001','004'):
        observation=json.loads((ROOT/'live/replies'/f'{n}.json').read_text())['reply']['observation']
        artifact=observation['native']['artifact'];expected.append(artifact['sha256'])
        require(hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest()==artifact['sha256'],'artifact hash mismatch')
    require([x['sha256'] for x in images]==expected,'actual model images mismatch retained PNGs')
    receipt=json.loads((ROOT/'live/replies/003.json').read_text())['reply']['receipt']
    require(receipt['outcome']=='SAFE_YIELD' and receipt['reason']=='association_changed','not actual typed yield')
    require(receipt['completed_transitions']==2 and receipt['pending_effect']['action']=='save','prefix/pending effect lost')
    book=load_workbook(ROOT/'live/sheet-1002086.xlsx',read_only=True,data_only=True)
    cells={cell.coordinate:cell.value for row in book.active for cell in row if cell.value is not None};book.close()
    require(cells=={'A1':317,'A2':529},'saved workbook mismatch')
    print(json.dumps({'status':'PASS','actual_model_images':images,'unique_provider_responses':len(usage_ids),'saved_cells':cells,'scope':'retained actual-source accounting and post-terminal workbook verification; not speed comparison'}))

if __name__=='__main__':main()
