import argparse,json,pathlib,sys

def main():
 ap=argparse.ArgumentParser();ap.add_argument('aggregate');a=ap.parse_args();agg=json.loads(pathlib.Path(a.aggregate).read_text());errs=[];counts={}
 for r in agg['rows']:
  k=(r['arm'],r['scenario']);counts[k]=counts.get(k,0)+1;t=r['task']; should = r['scenario']=='stable' or r['arm']=='recipient_only'
  if t['pid']!=r['spawn_pid'] or not t['same_pid_after_exec']:errs.append([r['case_id'],'pid'])
  if t['uid']!=65534 or t['gid']!=65534 or t['raw_path_ok'] or t['raw_path_error']!='OperationalError':errs.append([r['case_id'],'isolation'])
  if r['arm']=='recipient_only':
   if not t['cap_fd_exists'] or not t['cap_usable'] or t['cap_fd_count']!=1 or t['b_source']!='delegated_cap_scm_rights' or sorted(t['token'])!=['A'] or not r['grantor']['sent_fd'] or r['grantor']['revoked_before_exec_ack']: errs.append([r['case_id'],'recipient'])
  else:
   if not t['cap_fd_exists'] or t['cap_usable'] or t['cap_fd_count']!=0 or t['b_source']!='owner_socket' or sorted(t['token'])!=['A','B'] or r['grantor']['sent_fd'] or not r['grantor']['revoked_before_exec_ack']:errs.append([r['case_id'],'grantor'])
  if r['committed']!=should or r['final']['generation']!=(2 if should else 1) or len(r['final']['events'])!=(1 if should else 0):errs.append([r['case_id'],'effect'])
  if r['scenario']=='B_change' and r['final']['kv']['B']!={'value':'b2','revision':2}:errs.append([r['case_id'],'B'])
  if r['arm']=='grantor_revoke' and r['scenario']=='B_change' and r['mismatches']!=[{'key':'B','expected':1,'actual':2}]:errs.append([r['case_id'],'mismatch'])
 for arm in ['recipient_only','grantor_revoke']:
  for sc in ['stable','B_change']:
   if counts.get((arm,sc))!=3:errs.append(['count',arm,sc])
 dec='PASS_GRANTOR_REVOCATION_SCOPED' if not errs else 'FAIL_INTEGRITY';print(json.dumps({'decision':dec,'errors':errs,'counts':{f'{x}/{y}':counts.get((x,y),0) for x in ['recipient_only','grantor_revoke'] for y in ['stable','B_change']}},sort_keys=True));sys.exit(0 if not errs else 1)
if __name__=='__main__':main()
