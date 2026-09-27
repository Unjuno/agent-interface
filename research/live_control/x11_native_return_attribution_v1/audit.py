#!/usr/bin/env python3
"""Independent source/ABI/pixel/clock/load/schedule audit; no native code loading."""
import argparse,base64,hashlib,itertools,json,statistics
from pathlib import Path

TASK='X11-NATIVE-RETURN-ATTRIBUTION-20260916-001'
PERIOD=2_000_000
ARMS=('idle','process','thread')
FIELDS=('pre_native','xget','native_cleanup','post_native','copy','total')
def require(ok,msg):
    if not ok:raise ValueError(msg)
def expected_schedule():
    return [dict(pair=i,arm=a,count=(0,511,512,513,1023,1024)[i],order=3*i+j)
            for i,arms in enumerate(itertools.permutations(ARMS)) for j,a in enumerate(arms)]
def check_case(rec,cpus,n=32):
    require(rec['affinity']==[cpus['observer']],'observer affinity')
    rows=rec['rows']; require(len(rows)==n,'sample count')
    expected=rec['case']['count']; payloads=rec['pixels']; require(bool(payloads),'pixels absent')
    for dg,enc in payloads.items():
        b=base64.b64decode(enc,validate=True)
        require(len(b)==4096 and hashlib.sha256(b).hexdigest()==dg,'pixel digest')
        # Structurally independent oracle: three strided channels, not C byte loop.
        matches=sum(a==50 and z==50 and c==220 for a,z,c in zip(b[0::4],b[1::4],b[2::4]))
        require(matches==expected,'pixel semantics')
    due=10_000_000
    for i,r in enumerate(rows):
        require(len(r)==11,'row schema')
        require(all(type(r[j]) is int for j in list(range(9))+[10]),'timestamp type')
        require(r[0]==due,'due recurrence')
        require(0<r[0]<=r[1]<=r[2]<=r[3]<=r[4]<=r[5]<=r[6]<=r[7]<=r[10],'clock order')
        require(r[8]>=0,'CPU negative')
        require(r[9] in payloads,'pixel reference')
        if i:require(rows[i-1][10]<=r[1],'sample overlap')
        # Exact partition, all values in integer ns, including pre-X native setup.
        parts=[r[3]-r[1],r[4]-r[3],r[5]-r[4],r[6]-r[5],r[7]-r[6]]
        require(sum(parts)==r[7]-r[1],'partition closure')
        due+=PERIOD
        if due<r[10]-PERIOD:due+=((r[10]-due)//PERIOD+1)*PERIOD
    require(rec['end_ns']>=rec['origin_ns']+rows[-1][10],'case end')
    require(type(rec['observer_cpu_ns']) is int and rec['observer_cpu_ns']>0,'observer CPU')
    if rec['case']['arm']=='idle':require(rec['load'] is None,'idle load')
    else:
        ld=rec['load'];cpu=cpus['competitor']
        require(ld['cpu']==cpu and not ld['errors'] and ld['cleaned'],'load cleanup')
        for k in ('ready','before','after','final'):require(ld[k]['affinity']==[cpu],'load affinity')
        require(ld['before']['alive'] and ld['after']['alive'],'load liveness')
        require(ld['after']['ticks']>ld['before']['ticks'],'load CPU exposure')
        require(ld['final']['cpu_ns']>0 and ld['final']['iterations']>0,'load executed')
        require(ld['before']['at_ns']<=rec['origin_ns']+rows[0][1] and ld['after']['at_ns']>=rec['origin_ns']+rows[-1][7],'load envelope')
        require((ld['ready']['pid']==rec['observer_pid'])==(rec['case']['arm']=='thread'),'process/thread identity')
        if rec['case']['arm']=='process':require(ld['exitcode']==0 and not ld['forced'] and not ld['stderr'],'process exit')
    return True

def quantile(xs,p):
    ys=sorted(xs);u=(len(ys)-1)*p;a=int(u);f=u-a
    return ys[a]*(1-f)+ys[min(a+1,len(ys)-1)]*f

def derive(records):
    cases=[]
    for rec in records:
        vs={k:[] for k in FIELDS};shares=[];c_cpu=[]
        for r in rec['rows']:
            vals=(r[3]-r[1],r[4]-r[3],r[5]-r[4],r[6]-r[5],r[7]-r[6],r[7]-r[1])
            for k,v in zip(FIELDS,vals):vs[k].append(v)
            shares.append((r[6]-r[5])/max(r[6]-r[1],1));c_cpu.append(r[8])
        cases.append(dict(case=rec['case'],medians_ns={k:statistics.median(v) for k,v in vs.items()},
             p95_ns={k:quantile(v,.95) for k,v in vs.items()},max_ns={k:max(v) for k,v in vs.items()},
             median_post_share=statistics.median(shares),median_x_cpu_ns=statistics.median(c_cpu)))
    pairs=[]
    for i in range(6):
        arms={x['case']['arm']:x for x in cases if x['case']['pair']==i}
        if set(arms)!=set(ARMS):continue
        t=arms['thread'];p=arms['process'];rt=t['medians_ns']['post_native']/max(p['medians_ns']['post_native'],1)
        passed=t['medians_ns']['post_native']>=1_000_000 and t['median_post_share']>=.5 and rt>=3
        pairs.append(dict(pair=i,thread_post_ns=t['medians_ns']['post_native'],process_post_ns=p['medians_ns']['post_native'],ratio=rt,thread_share=t['median_post_share'],pass_pair=passed))
    count=sum(x['pass_pair'] for x in pairs)
    return dict(cases=cases,pairs=pairs,passing_pairs=count,
        decision='POST_NATIVE_DELAY_REPRODUCED_SCOPED' if len(pairs)==6 and count>=4 else 'HOLD_RETURN_ATTRIBUTION')

def audit(raw,plan,root):
    require(raw['task']==TASK and raw['mode']=='formal','identity/mode')
    require(not raw['errors'],'runtime errors')
    require(raw['sources']==raw['sources_after']==plan['sources'],'source record')
    for n,h in plan['sources'].items():require(hashlib.sha256((root/n).read_bytes()).hexdigest()==h,'source bytes')
    require(raw['plan_sha256']==hashlib.sha256((root/'prereg.json').read_bytes()).hexdigest(),'plan bytes')
    require(raw['binary_sha256']==plan['binary_sha256'],'binary identity')
    require(raw['environment']['cpus']==plan['cpus'],'CPU topology')
    require(raw['environment']['gil'] is True and raw['environment']['switch_interval']==plan['switch_interval'],'GIL mode')
    require([r['case'] for r in raw['records']]==expected_schedule()==plan['schedule'],'schedule')
    require(raw['server']['affinity']==raw['server']['affinity_after']==[plan['cpus']['server']],'server affinity')
    require(raw['server']['alive_after'] and raw['server']['reaped'] and raw['server']['exitcode']==0,'server lifecycle')
    for r in raw['records']:check_case(r,plan['cpus'])
    return dict(integrity_pass=True,cases=18,samples=576,summary=derive(raw['records']))

def verify_report(report,actual):require(report==actual,'derived report mismatch')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('raw');ap.add_argument('--out',required=True);ap.add_argument('--sha256');args=ap.parse_args()
    p=Path(args.raw);b=p.read_bytes()
    if args.sha256:require(hashlib.sha256(b).hexdigest()==args.sha256,'raw byte identity')
    root=Path(__file__).resolve().parent
    result=audit(json.loads(b),json.loads((root/'prereg.json').read_text()),root)
    result['raw_sha256']=hashlib.sha256(b).hexdigest()
    Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['summary']['decision'],result['summary']['passing_pairs'],'/6')
if __name__=='__main__':main()
