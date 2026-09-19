import json, random
from pathlib import Path
from frontier import frontier_pass,direct_pass,deficit,min_pure_width,min_lower_fixed_upper_inward
ROOT=Path(__file__).resolve().parent
A,B=1,4
V38=(990987,4039878)
V39=(2151534,8452733)
SEED=159220260918001

def one(W,U,dW,dU):
    f=frontier_pass(W,U,dW,dU,A,B); d=direct_pass(W,U,dW,dU,A,B)
    return f,d

def main():
    mismatches=[]; rows=0
    # exhaustive 1ms grid in a 0..70ms inward neighborhood for each retained point
    for label,(W,U) in [('v38',V38),('v39',V39)]:
        for dW in range(0,70001,1000):
            if dW>W: continue
            for dU in range(0,70001,1000):
                if dU>=U: continue
                if W-dW>U-dU: continue
                f,d=one(W,U,dW,dU); rows+=1
                if f!=d: mismatches.append([label,dW,dU,f,d])
    rng=random.Random(SEED)
    random_rows=250000
    bases=[V38,V39]
    for i in range(random_rows):
        W,U=bases[i&1]
        dW=rng.randrange(W+1)
        max_du=min(U-1, U-(W-dW))
        dU=rng.randrange(max_du+1)
        f,d=one(W,U,dW,dU); rows+=1
        if f!=d: mismatches.append(['random',i,dW,dU,f,d])
    controls={}
    D=deficit(*V39,A,B)
    pw=min_pure_width(*V39,A,B)
    pu=min_lower_fixed_upper_inward(*V39,A,B)
    controls['v38_zero']=one(*V38,0,0)==(True,True)
    controls['v39_zero']=one(*V39,0,0)==(False,False)
    controls['deficit']=D==153403
    controls['pure_width_min']=pw==38351 and one(*V39,pw,0)==(True,True) and one(*V39,pw-1,0)==(False,False)
    controls['pure_upper_lower_fixed_min']=pu==51135 and one(*V39,pu,pu)==(True,True) and one(*V39,pu-1,pu-1)==(False,False)
    # mixed exact equality: find integer solution 4*dW-dU=D
    eq_dW=40000; eq_dU=4*eq_dW-D
    controls['equality']=eq_dU>=0 and one(*V39,eq_dW,eq_dU)==(True,True) and (4*eq_dW-eq_dU==D)
    controls['just_below']=one(*V39,eq_dW,eq_dU+1)==(False,False)
    controls['just_above']=one(*V39,eq_dW+1,eq_dU)==(True,True)
    invalid=0
    for args in [(*V39,0,0,0,4),(*V39,0,0,4,4),(*V39,0,V39[1],1,4),(*V39,V39[0]+1,0,1,4)]:
        try: frontier_pass(*args)
        except ValueError: invalid+=1
    controls['invalid_rejected']=invalid==4
    passed=(not mismatches) and all(controls.values())
    out={'task':'MAP01-OCCUPANCY-GATE-FRONTIER-20260918-001','formal_invocations':1,'reruns':0,
         'seed':SEED,'grid_plus_random_rows':rows,'random_rows':random_rows,'mismatches':len(mismatches),
         'controls':controls,'v38':{'W_us':V38[0],'U_us':V38[1],'zero_pass':one(*V38,0,0)[0]},
         'v39':{'W_us':V39[0],'U_us':V39[1],'zero_pass':one(*V39,0,0)[0],'weighted_deficit_us':D,
                 'min_pure_width_reduction_us':pw,'min_lower_fixed_upper_inward_us':pu},
         'decision':'PASS_OCCUPANCY_GATE_FRONTIER_SCOPED' if passed else 'FAIL_FRONTIER_EQUIVALENCE','pass':passed}
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if passed else 1)
if __name__=='__main__': main()
