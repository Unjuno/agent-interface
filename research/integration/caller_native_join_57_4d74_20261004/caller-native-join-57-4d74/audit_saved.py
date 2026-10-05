import pathlib,json,hashlib
root=pathlib.Path(__file__).resolve().parent;errors=[]
freeze=json.loads((root/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig'))
for f in freeze:
    p=root/pathlib.PureWindowsPath(f['Path']).name
    if hashlib.sha256(p.read_bytes()).hexdigest().upper()!=f['Hash']:errors.append('source:'+p.name)
j=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'));native=json.loads((root/'native_raw.json').read_text(encoding='utf8'))['tasks'][-1]['receipt']
for row,value in zip(j['rows'],[native,{'status':native['status']}]):
    if row['input_sha256']!=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest():errors.append('input identity')
    r=row['result']
    if r['input_authority']!='consumed_by_recorded_execute_stage':errors.append('authority')
    if row['case']=='full_native_receipt':
        if r['outcome']!='CALLER_FAILED' or row['callbacks']!=['saved_execute_callback'] or r['execution_progress'] is not None:errors.append('direct schema gate')
    else:
        if (r['outcome'],r['task_effect'],r['delivery'],r['execution_progress'])!=('TASK_NOT_VERIFIED','unavailable','confirmed',{'status':'completed'}):errors.append('projected result')
        if row['callbacks']!=['saved_execute_callback','saved_verify_callback']:errors.append('callback counts')
    if sum(e.get('event')=='adaptive_route_finished' for e in row['events'])!=1:errors.append('terminal count')
if j['native_input_calls']!=0 or j['model_calls']!=0:errors.append('scope')
print(json.dumps(dict(errors=errors,rows=2,scope='same-author saved-byte/control-flow audit, no native or original caller actor replay'),indent=2));raise SystemExit(bool(errors))
