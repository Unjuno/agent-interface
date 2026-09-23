from fractions import Fraction as F
import argparse,base64,gzip,hashlib,json,random
from pathlib import Path
SEED=191120260919001
HORIZON=4
MAX_DWELL={'A':6,'B':7}
def schedule(scale):
    rows=[]
    rows += [('A',2)]*(20*scale)
    rows += [('A',4)]*(20*scale)
    rows += [('A',6)]*(20*scale)
    rows += [('B',1)]*(20*scale)
    rows += [('B',5)]*(10*scale)
    rows += [('B',7)]*(10*scale)
    rng=random.Random(SEED+scale);rng.shuffle(rows);return rows
def pack(rows,path):
    raw=''.join(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n' for r in rows).encode()
    Path(path).write_text(base64.b64encode(gzip.compress(raw,mtime=0)).decode()+'\n')
    return hashlib.sha256(raw).hexdigest(),len(raw)
def summarize(vis):
    n=len(vis);ns={'A':0,'B':0};complete={'A':0,'B':0};cens={'A':0,'B':0};sum_complete={'A':0,'B':0}
    ids=set();bad_state=bad_action=bad_elapsed=0
    for r in vis:
        ids.add(r['episode_id']);s=r['next_state'];ns[s]+=1;bad_state+=int(r['state']!='S0');bad_action+=int(r['action']!='GO')
        if r['effect_status']=='COMPLETE':complete[s]+=1;sum_complete[s]+=r['effect_time_or_censor'];bad_elapsed+=int(r['effect_time_or_censor']>r['horizon'])
        elif r['effect_status']=='CENSORED':cens[s]+=1;bad_elapsed+=int(r['effect_time_or_censor']!=r['horizon'])
        else:bad_elapsed+=1
    pA=F(ns['A'],n);intervals={};completion_means={}
    for s in ('A','B'):
        base=F(sum_complete[s],ns[s]);c=F(cens[s],ns[s]);intervals[s]=(base+c*(HORIZON+1),base+c*MAX_DWELL[s]);completion_means[s]=F(sum_complete[s],complete[s])
    comp_total=complete['A']+complete['B'];withheld=F(complete['A'],comp_total)
    return {'rows':n,'unique_ids':len(ids),'next_counts':ns,'complete_counts':complete,'censor_counts':cens,'bad_state':bad_state,'bad_action':bad_action,'bad_elapsed':bad_elapsed,'pA':str(pA),'dwell_intervals':{k:[str(x) for x in v] for k,v in intervals.items()},'completion_means':{k:str(v) for k,v in completion_means.items()},'withheld_state_completed_A_fraction':str(withheld)}
def generate(scale,visible_path,oracle_path):
    vis=[];oracle=[]
    for i,(s,d) in enumerate(schedule(scale)):
        status='COMPLETE' if d<=HORIZON else 'CENSORED'
        vis.append({'episode_id':i,'state':'S0','action':'GO','next_state':s,'state_signal_time':0,'effect_status':status,'effect_time_or_censor':d if status=='COMPLETE' else HORIZON,'horizon':HORIZON})
        oracle.append({'episode_id':i,'next_state':s,'true_dwell':d})
    vh,vb=pack(vis,visible_path);oh,ob=pack(oracle,oracle_path);return vis,oracle,vh,vb,oh,ob
def controls(vis,oracle):
    def valid(v):
        if len(v)!=len(oracle) or len({r['episode_id'] for r in v})!=len(v):return False
        for r,o in zip(v,oracle):
            if r['episode_id']!=o['episode_id'] or r['next_state']!=o['next_state'] or r['state']!='S0' or r['action']!='GO' or r['horizon']!=HORIZON:return False
            exp='COMPLETE' if o['true_dwell']<=HORIZON else 'CENSORED'
            if r['effect_status']!=exp:return False
            if r['effect_time_or_censor']!=(o['true_dwell'] if exp=='COMPLETE' else HORIZON):return False
        return True
    muts=[]
    for kind in range(5):
        x=json.loads(json.dumps(vis))
        if kind==0:x[0]['next_state']='B' if x[0]['next_state']=='A' else 'A'
        elif kind==1:x[0]['effect_status']='CENSORED' if x[0]['effect_status']=='COMPLETE' else 'COMPLETE'
        elif kind==2:x[0]['horizon']=99
        elif kind==3:x[0]['episode_id']=x[1]['episode_id']
        else:x[0]['effect_time_or_censor']=99
        muts.append(not valid(x))
    return {'next_state_mutation':muts[0],'censor_mutation':muts[1],'horizon_mutation':muts[2],'id_mutation':muts[3],'elapsed_mutation':muts[4]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);ap.add_argument('--visible',required=True);ap.add_argument('--oracle',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();scale=1 if a.construction else 10
    vis,hidden,vh,vb,oh,ob=generate(scale,a.visible,a.oracle);s=summarize(vis);ctrl=controls(vis,hidden)
    expected_n=100 if a.construction else 1000;expected_A=60 if a.construction else 600;expected_B=40 if a.construction else 400
    truth_mean={'A':F(4),'B':F(7,2)}
    intA=tuple(F(x) for x in s['dwell_intervals']['A']);intB=tuple(F(x) for x in s['dwell_intervals']['B'])
    good=(s['rows']==expected_n and s['unique_ids']==expected_n and s['next_counts']=={'A':expected_A,'B':expected_B} and s['bad_state']==s['bad_action']==s['bad_elapsed']==0 and s['pA']=='3/5' and intA==(F(11,3),F(4)) and intB==(F(3),F(4)) and intA[0]<=truth_mean['A']<=intA[1] and intB[0]<=truth_mean['B']<=intB[1] and F(s['completion_means']['A'])<truth_mean['A'] and F(s['completion_means']['B'])<truth_mean['B'] and s['withheld_state_completed_A_fraction']=='2/3' and all(ctrl.values()))
    r={'construction':a.construction,'seed':SEED,'summary':s,'truth_means':{k:str(v) for k,v in truth_mean.items()},'visible_raw_sha256':vh,'visible_raw_bytes':vb,'oracle_raw_sha256':oh,'oracle_raw_bytes':ob,'corruption_controls':ctrl,'formal_invocations':0 if a.construction else 1,'reruns':0,'replacements':0,'tuning':0,'decision':('CONSTRUCTION_PASS' if a.construction and good else ('PASS_PROBABILISTIC_AUTOMATON_CALIBRATION_FIXTURE_SCOPED' if good else 'FAIL_INTEGRITY'))}
    raw=json.dumps(r,sort_keys=True,separators=(',',':')).encode();r['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r,indent=2,sort_keys=True))
if __name__=='__main__':main()
