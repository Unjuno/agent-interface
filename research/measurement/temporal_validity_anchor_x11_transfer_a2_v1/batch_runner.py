import argparse,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'parent'
sys.path.insert(0,str(PARENT))
import runner as parent_runner

TASK='TEMPORAL-SPECULATION-VALIDITY-ANCHOR-X11-TRANSFER-A2-20260918-002'
DELAYS=[130,145,160]*8
FORMAL_STARTS=set(range(0,24,3))

def source_check():
    m=json.loads((HERE/'parent_source_map.json').read_text())['files']
    rows=[]
    for name,expected in m.items():
        actual=hashlib.sha256((PARENT/name).read_bytes()).hexdigest()
        rows.append({'name':name,'expected':expected,'actual':actual,'match':actual==expected})
    if not all(x['match'] for x in rows): raise RuntimeError('parent source mismatch')
    return rows

def run_pair(global_pair,delay_ms,base_display=1330):
    order=('SOURCE_APPLIED','CURRENT_EVIDENCE') if global_pair%2==0 else ('CURRENT_EVIDENCE','SOURCE_APPLIED')
    arms=[]
    for j,anchor in enumerate(order):
        arms.append(parent_runner.one(base_display+global_pair*2+j,anchor,delay_ms))
    return {'pair':global_pair,'delay_ms':delay_ms,'arms':arms}

def formal(start,count,out):
    if start not in FORMAL_STARTS or count!=3 or start+count>24: raise ValueError('formal range')
    p=Path(out)
    if p.exists(): raise FileExistsError(out)
    source_check()
    rows=[run_pair(i,DELAYS[i]) for i in range(start,start+count)]
    result={'task':TASK,'parent_task':'TEMPORAL-SPECULATION-VALIDITY-ANCHOR-X11-TRANSFER-20260918-001',
            'batch_index':start//3,'start_pair':start,'end_pair_exclusive':start+count,
            'formal_batch_invocation':1,'batch_reruns':0,'rows':rows}
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},sort_keys=True))

def construction(out):
    p=Path(out)
    if p.exists(): raise FileExistsError(out)
    source_check()
    pairs=[]
    for k,(pair,delay) in enumerate(((100,20),(101,25))):
        # construction uses disjoint display IDs and IDs; no formal row is consumed
        order=('SOURCE_APPLIED','CURRENT_EVIDENCE') if pair%2==0 else ('CURRENT_EVIDENCE','SOURCE_APPLIED')
        arms=[parent_runner.one(1600+k*2+j,anchor,delay) for j,anchor in enumerate(order)]
        pairs.append({'pair':pair,'delay_ms':delay,'arms':arms})
    p.write_text(json.dumps({'task':TASK,'mode':'construction','formal_rows':0,'pairs':pairs},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'construction_pairs':len(pairs),'formal_rows':0}))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--start',type=int);ap.add_argument('--count',type=int,default=3);ap.add_argument('--out',required=True);ap.add_argument('--construction',action='store_true');a=ap.parse_args()
    if a.construction: construction(a.out)
    else: formal(a.start,a.count,a.out)
if __name__=='__main__':main()
