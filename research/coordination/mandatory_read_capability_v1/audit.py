import argparse,json,pathlib,sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('aggregate'); args=ap.parse_args(); agg=json.loads(pathlib.Path(args.aggregate).read_text()); errors=[]
    counts={}
    for r in agg['rows']:
        key=(r['arm'],r['scenario']); counts[key]=counts.get(key,0)+1
        expected_token=['A'] if r['arm']=='unrestricted' else ['A','B']
        if sorted(r['task']['token']) != expected_token: errors.append([r['case_id'],'token',r['task']['token']])
        if r['arm']=='unrestricted' and not r['task']['raw_b_ok']: errors.append([r['case_id'],'raw_should_work'])
        if r['arm']=='mediated' and r['task']['raw_b_ok']: errors.append([r['case_id'],'raw_escape'])
        if r['arm']=='mediated' and r['task']['raw_b_error']!='OperationalError': errors.append([r['case_id'],'wrong_raw_error',r['task']['raw_b_error']])
        if r['db_mode']!='0o600' or r['private_mode']!='0o700' or r['db_uid']!=0 or r['private_uid']!=0: errors.append([r['case_id'],'capability_metadata'])
        should_commit = r['scenario']=='stable' or r['arm']=='unrestricted'
        if r['committed'] != should_commit: errors.append([r['case_id'],'commit',r['committed'],should_commit])
        if r['final']['generation'] != (2 if should_commit else 1): errors.append([r['case_id'],'generation'])
        if len(r['final']['events']) != (1 if should_commit else 0): errors.append([r['case_id'],'events'])
        if r['scenario']=='B_change' and r['final']['kv']['B'] != {'value':'b2','revision':2}: errors.append([r['case_id'],'B_final'])
        if r['arm']=='mediated' and r['scenario']=='B_change':
            if r['mismatches'] != [{'key':'B','expected':1,'actual':2}]: errors.append([r['case_id'],'mismatch',r['mismatches']])
    for arm in ['unrestricted','mediated']:
        for scenario in ['stable','B_change']:
            if counts.get((arm,scenario)) != 3: errors.append(['count',arm,scenario,counts.get((arm,scenario))])
    decision='PASS_MANDATORY_READ_MEDIATION_SCOPED' if not errors else 'FAIL_INTEGRITY'
    out={'decision':decision,'errors':errors,'counts':{f'{a}/{s}':counts.get((a,s),0) for a in ['unrestricted','mediated'] for s in ['stable','B_change']}}
    print(json.dumps(out,sort_keys=True)); sys.exit(0 if not errors else 1)
if __name__=='__main__': main()
