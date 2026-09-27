#!/opt/pyvenv/bin/python3
import argparse,json,pathlib
import run as parent
P=pathlib.Path(__file__).parent

def owned_pairs(batch):
    if batch not in range(4): raise ValueError(batch)
    return list(range(batch*5,(batch+1)*5))

def partition_self_test():
    all_ids=[x for b in range(4) for x in owned_pairs(b)]
    assert all_ids==list(range(20))
    assert len(set(all_ids))==20
    return {'pairs':all_ids,'unique':len(set(all_ids)),'batches':4}

def execute(batch,out):
    pairs=owned_pairs(batch); rows=[]
    for gid in pairs:
        order=['file','dgram'] if gid%2==0 else ['dgram','file']
        for j,tr in enumerate(order):
            rows.append(parent.run_case(f'p{gid:03d}-{tr}',tr,300+gid*2+j))
    obj={'batch':batch,'pair_start':pairs[0],'pair_end_exclusive':pairs[-1]+1,'pairs':pairs,'rows':rows}
    pathlib.Path(out).write_text(json.dumps(obj,indent=2,sort_keys=True))
    return obj

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--batch',type=int); ap.add_argument('--out'); ap.add_argument('--self-test',action='store_true'); a=ap.parse_args()
    if a.self_test:
        print(json.dumps(partition_self_test(),sort_keys=True)); return
    if a.batch is None or not a.out: raise SystemExit('need --batch and --out')
    obj=execute(a.batch,a.out); print(json.dumps({'batch':obj['batch'],'rows':len(obj['rows']),'pairs':obj['pairs']}))
if __name__=='__main__': main()
