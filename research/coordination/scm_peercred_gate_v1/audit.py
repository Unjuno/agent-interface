import argparse,json,pathlib,sys
ap=argparse.ArgumentParser(); ap.add_argument('aggregate'); args=ap.parse_args(); a=json.loads(pathlib.Path(args.aggregate).read_text()); errs=[]; counts={}
for r in a['rows']:
    k=(r['arm'],r['scenario']); counts[k]=counts.get(k,0)+1; t=r['task']; b=r['broker']
    if t['uid']!=65534 or t['gid']!=65534: errs.append([r['case_id'],'uidgid'])
    if t['raw_path_ok'] or t['raw_path_error']!='OperationalError': errs.append([r['case_id'],'pathname_boundary'])
    if any(str(v).endswith('/state.db') for v in t['startup_fd_targets'].values()): errs.append([r['case_id'],'startup_db_fd'])
    if r['db_mode']!='0o600' or r['private_mode']!='0o700' or r['db_uid']!=0 or r['private_uid']!=0: errs.append([r['case_id'],'fs_metadata'])
    if b.get('peer_uid')!=65534 or b.get('peer_gid')!=65534: errs.append([r['case_id'],'peercred',b])
    if r['arm']=='unguarded':
        if sorted(t['token'])!=['A'] or t['b_source']!='scm_rights_fd' or t['broker_fd_count']!=1 or not b['sent_fd'] or not b['allowed']: errs.append([r['case_id'],'unguarded_source'])
    else:
        if sorted(t['token'])!=['A','B'] or t['b_source']!='owner_socket' or t['broker_fd_count']!=0 or b['sent_fd'] or b['allowed']: errs.append([r['case_id'],'guard_source'])
        if t['broker_msg']!='D': errs.append([r['case_id'],'guard_denial_msg',t['broker_msg']])
    should_commit = r['scenario']=='stable' or r['arm']=='unguarded'
    if r['committed']!=should_commit: errs.append([r['case_id'],'commit'])
    if r['final']['generation']!=(2 if should_commit else 1): errs.append([r['case_id'],'generation'])
    if len(r['final']['events'])!=(1 if should_commit else 0): errs.append([r['case_id'],'events'])
    if r['scenario']=='B_change' and r['final']['kv']['B']!={'value':'b2','revision':2}: errs.append([r['case_id'],'B_final'])
    if r['arm']=='peer_guard' and r['scenario']=='B_change' and r['mismatches']!=[{'key':'B','expected':1,'actual':2}]: errs.append([r['case_id'],'mismatch'])
for arm in ['unguarded','peer_guard']:
  for sc in ['stable','B_change']:
    if counts.get((arm,sc))!=3: errs.append(['count',arm,sc,counts.get((arm,sc))])
dec='PASS_SO_PEERCRED_GATE_SCOPED' if not errs else 'FAIL_INTEGRITY'
print(json.dumps({'decision':dec,'errors':errs,'counts':{f'{x}/{y}':counts.get((x,y),0) for x in ['unguarded','peer_guard'] for y in ['stable','B_change']}},sort_keys=True)); sys.exit(0 if not errs else 1)
