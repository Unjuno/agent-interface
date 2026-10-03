import pathlib,json,hashlib
root=pathlib.Path(__file__).resolve().parent;errors=[]
for item in json.loads((root/'SOURCE_FREEZE.json').read_text(encoding='utf-8-sig')):
    p=root/pathlib.PureWindowsPath(item['Path']).name
    if hashlib.sha256(p.read_bytes()).hexdigest().upper()!=item['Hash']:errors.append('source:'+p.name)
j=json.loads((root/'first-result.json').read_text(encoding='utf-8-sig'))
expected={'preinput_refusal':(0,False,'not_attempted','none'),'partial_execution_failure':(1,True,'delivery_uncertain','consumed_by_recorded_execute_stage'),'release_unverified_after_prefix':(33,True,'delivery_uncertain','consumed_by_recorded_execute_stage')}
if len(j['rows'])!=3:errors.append('rows')
for row in j['rows']:
    n,started,delivery,authority=expected[row['case']];r=row['result'];d=row['decision']
    if type(d['completed_actions']) is not int or d['completed_actions']!=n or d['input_dispatched'] is not started:errors.append('typed decision')
    if r['execution_progress']!=d or r['outcome']!='EXECUTION_INCOMPLETE' or r['delivery']!=delivery or r['input_authority']!=authority:errors.append('mapped state')
    if row['callbacks']!=['saved_decision_execute'] or r['accounting']['attempted_calls']!=0:errors.append('calls')
    if sum(e.get('event')=='adaptive_route_finished' for e in row['events'])!=1:errors.append('terminal')
if j['native_input_calls']!=0:errors.append('native scope')
print(json.dumps(dict(errors=errors,rows=3,scope='same-author saved contract audit, not real native failure or production projection validation'),indent=2));raise SystemExit(bool(errors))
