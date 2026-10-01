import argparse,json,pathlib

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',required=True); ap.add_argument('--chunks-root',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    plan=json.loads(pathlib.Path(args.plan).read_text()); root=pathlib.Path(args.chunks_root); rows=[]
    nchunks=(len(plan['schedule'])+plan['chunk_size']-1)//plan['chunk_size']
    for i in range(nchunks):
        r=json.loads((root/f'chunk-{i}'/'chunk_result.json').read_text()); rows.extend(r['rows'])
    ids=[r['case_id'] for r in rows]; expected=[x['id'] for x in plan['schedule']]
    if ids != expected: raise RuntimeError(f'row order mismatch {ids} != {expected}')
    if len(ids)!=len(set(ids)): raise RuntimeError('duplicate IDs')
    agg={'task':plan['task'],'rows':rows,'formal_reruns':0,'supervision':'six independent two-case chunks'}
    pathlib.Path(args.out).write_text(json.dumps(agg,sort_keys=True,indent=2)+'\n')
    print(json.dumps(agg,sort_keys=True))
if __name__=='__main__': main()
