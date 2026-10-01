import argparse,json,pathlib,sys
p=argparse.ArgumentParser(); p.add_argument('aggregate'); a=p.parse_args(); agg=json.loads(pathlib.Path(a.aggregate).read_text())
errors=[]; counts={'seq_order_arrival':0,'reverse_arrival':0}
for r in agg['rows']:
    arm=r['arm']; counts[arm]=counts.get(arm,0)+1
    if r['ack_first']!='ACK_APPLIED' or r['ack_replay']!='ACK_ALREADY_APPLIED': errors.append([r['case_id'],'ack'])
    if any(w['returncode']!=0 for w in r['workers'].values()): errors.append([r['case_id'],'worker_rc'])
    if arm=='seq_order_arrival':
        if r['arrival_order']!=[4,5]: errors.append([r['case_id'],'arrival'])
        if r['pending_before_ack']!=['E4','E5']: errors.append([r['case_id'],'pending_before',r['pending_before_ack']])
        if r['drain']!=[{'event_id':'E4','status':'EVENT_ACCEPTED'},{'event_id':'E5','status':'EVENT_ACCEPTED'}]: errors.append([r['case_id'],'drain',r['drain']])
        if r['final']!={'ack':2,'consumer':['E3','E4','E5'],'pending':[]}: errors.append([r['case_id'],'final',r['final']])
    elif arm=='reverse_arrival':
        if r['arrival_order']!=[5,4]: errors.append([r['case_id'],'arrival'])
        if r['pending_before_ack']!=['E5','E4']: errors.append([r['case_id'],'pending_before',r['pending_before_ack']])
        if r['drain']!=[{'event_id':'E5','status':'EVENT_ACCEPTED'},{'event_id':'E4','status':'EVENT_NON_MONOTONIC'}]: errors.append([r['case_id'],'drain',r['drain']])
        if r['final']!={'ack':2,'consumer':['E3','E5'],'pending':['E4']}: errors.append([r['case_id'],'final',r['final']])
    else: errors.append([r['case_id'],'arm'])
if counts!={'seq_order_arrival':4,'reverse_arrival':4}: errors.append(['counts',counts])
decision='RETAIN_FIFO2_PRODUCER_ORDER_BOUNDARY_SCOPED' if not errors else 'FAIL_INTEGRITY'
out={'decision':decision,'counts':counts,'errors':errors,'formal_reruns':0}
print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
