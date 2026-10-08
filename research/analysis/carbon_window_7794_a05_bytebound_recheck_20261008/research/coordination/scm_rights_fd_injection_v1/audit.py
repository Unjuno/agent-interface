import argparse,json,pathlib,sys
ap=argparse.ArgumentParser(); ap.add_argument('aggregate'); args=ap.parse_args(); a=json.loads(pathlib.Path(args.aggregate).read_text()); errs=[]; counts={}
for r in a['rows']:
    k=(r['arm'],r['scenario']); counts[k]=counts.get(k,0)+1
    t=r['task']
    if t['uid']!=65534 or t['gid']!=65534: errs.append([r['case_id'],'uidgid'])
    if t['raw_path_ok'] or t['raw_path_error']!='OperationalError': errs.append([r['case_id'],'pathname_boundary'])
    if any(str(v).endswith('/state.db') for v in t['startup_fd_targets'].values()): errs.append([r['case_id'],'startup_db_fd',t['startup_fd_targets']])
    if r['db_mode']!='0o600' or r['private_mode']!='0o700' or r['db_uid']!=0 or r['private_uid']!=0: errs.append([r['case_id'],'fs_metadata'])
    if r['arm']=='control':
        if sorted(t['token'])!=['A','B'] or t['b_source']!='owner_socket' or t['broker_fd_count']!=0 or r['broker']['sent_fd']: errs.append([r['case_id'],'control_source'])
    else:
        if sorted(t['token'])!=['A'] or t['b_source']!='scm_rights_fd' or t['broker_fd_count']!=1 or not r['broker']['sent_fd']: errs.append([r['case_id'],'inject_source'])
    should_commit = r['scenario']=='stable' or r['arm']=='inject_fd'
    if r['committed']!=should_commit: errs.append([r['case_id'],'commit'])
    if r['final']['generation']!=(2 if should_commit else 1): errs.append([r['case_id'],'generation'])
    if len(r['final']['events'])!=(1 if should_commit else 0): errs.append([r['case_id'],'events'])
    if r['scenario']=='B_change' and r['final']['kv']['B']!={'value':'b2','revision':2}: errs.append([r['case_id'],'B_final'])
    if r['arm']=='control' and r['scenario']=='B_change' and r['mismatches']!=[{'key':'B','expected':1,'actual':2}]: errs.append([r['case_id'],'mismatch'])
for arm in ['control','inject_fd']:
  for sc in ['stable','B_change']:
    if counts.get((arm,sc))!=3: errs.append(['count',arm,sc,counts.get((arm,sc))])
dec='RETAIN_SCM_RIGHTS_INJECTION_BOUNDARY_SCOPED' if not errs else 'FAIL_INTEGRITY'
print(json.dumps({'decision':dec,'errors':errs,'counts':{f'{a}/{s}':counts.get((a,s),0) for a in ['control','inject_fd'] for s in ['stable','B_change']}},sort_keys=True)); sys.exit(0 if not errs else 1)
