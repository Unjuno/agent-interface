import json, pathlib, sys
rows=json.loads(pathlib.Path(sys.argv[1]).read_text())['rows']; errs=[]
for r in rows:
    p=r['policy']; pre=r['postkill']; ctl=r['controls']; fin=r['final']
    if r['kill_rc']!=-9: errs.append([r['id'],'kill_rc'])
    if p=='single':
        if pre['pending']!=['E4']: errs.append([r['id'],'single_pending',pre])
        if ctl.get('e5_offer_after_restart')!='PRODUCER_PENDING_FULL': errs.append([r['id'],'single_e5'])
        if r['drain']!=['EVENT_ACCEPTED','NO_PENDING']: errs.append([r['id'],'single_drain',r['drain']])
        if fin['consumer']!=['E3','E4']: errs.append([r['id'],'single_final',fin])
    else:
        if pre['pending']!=['E4','E5']: errs.append([r['id'],'fifo_pending',pre])
        if ctl.get('e6')!='PRODUCER_PENDING_FULL' or ctl.get('e5_early')!='PENDING_HEAD_REQUIRED': errs.append([r['id'],'fifo_controls',ctl])
        if r['drain']!=['EVENT_ACCEPTED','EVENT_ACCEPTED']: errs.append([r['id'],'fifo_drain',r['drain']])
        if fin['consumer']!=['E3','E4','E5']: errs.append([r['id'],'fifo_final',fin])
    if ctl['ack1']!='ACK_APPLIED' or ctl['ack_replay']!='ACK_ALREADY_APPLIED': errs.append([r['id'],'ack',ctl])
    if fin['pending']!=[] or r['restart']!=fin: errs.append([r['id'],'restart'])
counts={p:sum(r['policy']==p for r in rows) for p in ('single','fifo2')}
if counts!={'single':3,'fifo2':3}: errs.append(['counts',counts])
out={'decision':'PASS_DURABLE_FIFO2_PENDING_SCOPED' if not errs else 'FAIL_INTEGRITY','errors':errs,'counts':counts}
print(json.dumps(out,sort_keys=True)); sys.exit(bool(errs))
