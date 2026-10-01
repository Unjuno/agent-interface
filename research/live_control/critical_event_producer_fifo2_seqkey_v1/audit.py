import argparse,json,pathlib,sys
p=argparse.ArgumentParser(); p.add_argument('aggregate'); a=p.parse_args(); agg=json.loads(pathlib.Path(a.aggregate).read_text())
errors=[]; counts={}
for r in agg['rows']:
    key=(r['policy'],r['arrival']); counts[key]=counts.get(key,0)+1
    if r['ack_first']!='ACK_APPLIED' or r['ack_replay']!='ACK_ALREADY_APPLIED': errors.append([r['case_id'],'ack'])
    if any(w['returncode']!=0 for w in r['workers'].values()): errors.append([r['case_id'],'worker_rc'])
    if r['policy']=='arrival_pos' and r['arrival']=='reverse_order':
        if r['pending_before_ack']!=['E5','E4']: errors.append([r['case_id'],'baseline_pending',r['pending_before_ack']])
        if r['drain']!=[{'event_id':'E5','status':'EVENT_ACCEPTED'},{'event_id':'E4','status':'EVENT_NON_MONOTONIC'}]: errors.append([r['case_id'],'baseline_drain',r['drain']])
        if r['final']!={'ack':2,'consumer':['E3','E5'],'pending':['E4']}: errors.append([r['case_id'],'baseline_final',r['final']])
    else:
        if r['pending_before_ack']!=['E4','E5']: errors.append([r['case_id'],'pending',r['pending_before_ack']])
        if r['drain']!=[{'event_id':'E4','status':'EVENT_ACCEPTED'},{'event_id':'E5','status':'EVENT_ACCEPTED'}]: errors.append([r['case_id'],'drain',r['drain']])
        if r['final']!={'ack':2,'consumer':['E3','E4','E5'],'pending':[]}: errors.append([r['case_id'],'final',r['final']])
expected={(p,a):3 for p in ['arrival_pos','sequence_pos'] for a in ['seq_order','reverse_order']}
if counts!=expected: errors.append(['counts', {f'{k[0]}/{k[1]}':v for k,v in counts.items()}])
decision='PASS_SEQUENCE_KEYED_FIFO2_SCOPED' if not errors else 'FAIL_INTEGRITY'
out={'decision':decision,'counts':{f'{k[0]}/{k[1]}':v for k,v in sorted(counts.items())},'errors':errors,'formal_reruns':0}
print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
