import argparse,json,pathlib,sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('aggregate'); a=ap.parse_args(); agg=json.loads(pathlib.Path(a.aggregate).read_text()); errors=[]; counts={}
    for r in agg['rows']:
        key=(r['arm'],r['scenario']); counts[key]=counts.get(key,0)+1
        s=r['supervisor']; t=s['task']; tr=s['trace']
        if t['pid']!=s['helper_pid'] or not t['same_pid_after_exec']: errors.append([r['case_id'],'pid'])
        if t['uid']!=65534 or t['gid']!=65534 or t['raw_path_ok'] or t['raw_path_error']!='OperationalError': errors.append([r['case_id'],'isolation'])
        if not t['cap_fd_exists']: errors.append([r['case_id'],'alias_missing'])
        if r['arm']=='no_observer':
            if tr['seize'] or tr['exec_stop'] or tr['event'] is not None or r['grantor_revoked_on_exec']: errors.append([r['case_id'],'baseline_trace'])
            if not t['cap_usable'] or t['cap_fd_count']!=1 or t['b_source']!='delegated_cap_scm_rights' or sorted(t['token'])!=['A'] or not r['broker'] or not r['broker']['sent_fd']: errors.append([r['case_id'],'baseline_cap'])
            if r['owner_reads']!=['A']: errors.append([r['case_id'],'baseline_owner_reads',r['owner_reads']])
            should=True
        else:
            if not tr['seize'] or not tr['exec_stop'] or tr['event']!=4 or tr['stop_signal']!=5 or not r['grantor_revoked_on_exec']: errors.append([r['case_id'],'ptrace_exec'])
            if any(sig!=13 for sig in tr.get('post_exec_stops',[])): errors.append([r['case_id'],'unexpected_post_exec_stop',tr.get('post_exec_stops')])
            if t['cap_usable'] or t['cap_fd_count']!=0 or t['b_source']!='owner_socket' or sorted(t['token'])!=['A','B'] or r['broker'] is not None: errors.append([r['case_id'],'ptrace_cap'])
            if r['owner_reads']!=['A','B']: errors.append([r['case_id'],'ptrace_owner_reads',r['owner_reads']])
            should = r['scenario']=='stable'
        if r['committed']!=should or r['final']['generation']!=(2 if should else 1) or len(r['final']['events'])!=(1 if should else 0): errors.append([r['case_id'],'effect'])
        if r['scenario']=='B_change' and r['final']['kv']['B']!={'value':'b2','revision':2}: errors.append([r['case_id'],'B_final'])
        if r['arm']=='ptrace_exec_revoke' and r['scenario']=='B_change' and r['mismatches']!=[{'key':'B','expected':1,'actual':2}]: errors.append([r['case_id'],'mismatch',r['mismatches']])
    for arm in ['no_observer','ptrace_exec_revoke']:
        for sc in ['stable','B_change']:
            if counts.get((arm,sc))!=3: errors.append(['count',arm,sc,counts.get((arm,sc))])
    decision='PASS_KERNEL_EXEC_REVOCATION_SCOPED' if not errors else 'FAIL_INTEGRITY'
    out={'decision':decision,'errors':errors,'counts':{f'{x}/{y}':counts.get((x,y),0) for x in ['no_observer','ptrace_exec_revoke'] for y in ['stable','B_change']}}
    print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
if __name__=='__main__': main()
