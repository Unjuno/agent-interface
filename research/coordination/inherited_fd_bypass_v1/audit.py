import argparse,json,pathlib,sys
ap=argparse.ArgumentParser(); ap.add_argument('aggregate'); args=ap.parse_args(); a=json.loads(pathlib.Path(args.aggregate).read_text()); errs=[]; counts={}
for r in a['rows']:
    k=(r['arm'],r['scenario']); counts[k]=counts.get(k,0)+1
    if r['task']['uid']!=65534 or r['task']['gid']!=65534: errs.append([r['case_id'],'uidgid'])
    if r['task']['raw_path_ok'] or r['task']['raw_path_error']!='OperationalError': errs.append([r['case_id'],'pathname_boundary'])
    if r['db_mode']!='0o600' or r['private_mode']!='0o700' or r['db_uid']!=0 or r['private_uid']!=0: errs.append([r['case_id'],'fs_metadata'])
    exp_keys=['A','B'] if r['arm']=='no_fd' else ['A']
    if sorted(r['task']['token'])!=exp_keys: errs.append([r['case_id'],'token',r['task']['token']])
    exp_source='socket' if r['arm']=='no_fd' else 'fd_deserialize'
    if r['task']['b_source']!=exp_source: errs.append([r['case_id'],'source',r['task']['b_source']])
    should_commit = r['scenario']=='stable' or r['arm']=='leaked_fd'
    if r['committed']!=should_commit: errs.append([r['case_id'],'commit'])
    if r['final']['generation']!=(2 if should_commit else 1): errs.append([r['case_id'],'generation'])
    if len(r['final']['events'])!=(1 if should_commit else 0): errs.append([r['case_id'],'events'])
    if r['scenario']=='B_change' and r['final']['kv']['B']!={'value':'b2','revision':2}: errs.append([r['case_id'],'B_final'])
    if r['arm']=='no_fd' and r['scenario']=='B_change' and r['mismatches']!=[{'key':'B','expected':1,'actual':2}]: errs.append([r['case_id'],'mismatch'])
for arm in ['no_fd','leaked_fd']:
  for sc in ['stable','B_change']:
    if counts.get((arm,sc))!=3: errs.append(['count',arm,sc,counts.get((arm,sc))])
dec='RETAIN_INHERITED_FD_BYPASS_BOUNDARY_SCOPED' if not errs else 'FAIL_INTEGRITY'
print(json.dumps({'decision':dec,'errors':errs,'counts':{f'{a}/{s}':counts.get((a,s),0) for a in ['no_fd','leaked_fd'] for s in ['stable','B_change']}},sort_keys=True)); sys.exit(0 if not errs else 1)
