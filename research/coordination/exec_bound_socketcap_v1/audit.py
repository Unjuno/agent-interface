import argparse,json,pathlib,sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('aggregate'); a=ap.parse_args(); agg=json.loads(pathlib.Path(a.aggregate).read_text()); errors=[]; counts={}
    for r in agg['rows']:
        k=(r['arm'],r['scenario']); counts[k]=counts.get(k,0)+1; t=r['task']
        if t['pid']!=r['spawn_pid'] or not t['same_pid_after_exec']: errors.append([r['case_id'],'exec_pid'])
        if t['uid']!=65534 or t['gid']!=65534: errors.append([r['case_id'],'uidgid'])
        if t['raw_path_ok'] or t['raw_path_error']!='OperationalError': errors.append([r['case_id'],'raw_path'])
        if r['db_mode']!='0o600' or r['private_mode']!='0o700' or r['db_uid']!=0 or r['private_uid']!=0: errors.append([r['case_id'],'modes'])
        if r['arm']=='persistent_cap':
            if not t['cap_available'] or t['cap_fd_count']!=1 or t['b_source']!='inherited_cap_scm_rights' or sorted(t['token'])!=['A'] or not r['cap_broker']['sent_fd']: errors.append([r['case_id'],'persistent_cap'])
            should=True
        else:
            if t['cap_available'] or t['cap_error']!='OSError' or t['cap_fd_count']!=0 or t['b_source']!='owner_socket' or sorted(t['token'])!=['A','B'] or r['cap_broker']['sent_fd']: errors.append([r['case_id'],'cloexec_cap'])
            should = r['scenario']=='stable'
        if r['committed']!=should or r['final']['generation']!=(2 if should else 1) or len(r['final']['events'])!=(1 if should else 0): errors.append([r['case_id'],'effect'])
        if r['scenario']=='B_change' and r['final']['kv']['B']!={'value':'b2','revision':2}: errors.append([r['case_id'],'B_final'])
        if r['arm']=='cloexec_cap' and r['scenario']=='B_change' and r['mismatches']!=[{'key':'B','expected':1,'actual':2}]: errors.append([r['case_id'],'mismatch'])
    decision='PASS_EXEC_BOUND_CAPABILITY_SCOPED' if not errors else 'FAIL_INTEGRITY'
    out={'decision':decision,'errors':errors,'counts':{f'{x}/{y}':counts.get((x,y),0) for x in ['persistent_cap','cloexec_cap'] for y in ['stable','B_change']}}
    print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
if __name__=='__main__': main()
