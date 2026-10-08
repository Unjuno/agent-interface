import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text());I=json.loads((R/'INPUTS.json').read_text());out=json.loads((R/'output/RESULT.json').read_text());F=json.loads((R/'FREEZE.json').read_text());errors=[];cli_digest=F['files'].pop(P['CLI'])
for name,digest in F['files'].items():
    if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:errors.append('source:'+name)
if out['attempted_calls']!=len(out['rows']) or out['censored_cases']!=4-len(out['rows']):errors.append('denominator')
for idx,row in enumerate(out['rows']):
    spec=I[idx];name=spec['case'];events=[json.loads(l) for l in (R/'output'/ (name+'.stdout.jsonl')).read_bytes().splitlines()];usage=[e.get('usage') for e in events if e.get('type')=='turn.completed']
    if row['case']!=name or row['events']!=events or usage!=row['usage_reports']:errors.append('raw_join:'+name)
    if row['elapsed_ns']<0:errors.append('clock')
    if row['gate']=='PASS_KNOWN_RECEIPT_INTERPRETATION':
        if row['exit_code']!=0 or row['tool_items'] or row['answer']['action']!=spec['expected']:errors.append('gate:'+name)
    elif idx!=len(out['rows'])-1 or out['stop']!=name:errors.append('stop_boundary')
print(json.dumps({'errors':errors,'attempted_calls':out['attempted_calls'],'censored_cases':out['censored_cases'],'source_disposition':out['disposition'],'scope':'saved literal provider events and accounting, not new model/native/actor replay; CLI digest checked on host freeze only'},indent=2));raise SystemExit(bool(errors))
