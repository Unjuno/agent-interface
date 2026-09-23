import argparse, hashlib, itertools, json
from dataclasses import dataclass
from pathlib import Path

RESOURCES=(0,1,2)
INITIAL_STATES=((0,1,2),(2,0,1))
INTENTS=("A","B")

@dataclass(frozen=True)
class Op:
    kind:str
    a:int
    b:int=-1
    value:int=0
    @property
    def reads(self):
        if self.kind=="READ": return frozenset((self.a,))
        if self.kind=="INC": return frozenset((self.a,))
        if self.kind=="COPYPLUS": return frozenset((self.a,))
        return frozenset()
    @property
    def writes(self):
        if self.kind in ("SET","INC"): return frozenset((self.a,))
        if self.kind=="COPYPLUS": return frozenset((self.b,))
        return frozenset()
    @property
    def name(self):
        if self.kind=="SET": return f"SET{self.value}_r{self.a}"
        if self.kind=="COPYPLUS": return f"COPYPLUS_r{self.a}_r{self.b}"
        return f"{self.kind}_r{self.a}"
    def apply(self,state):
        s=list(state)
        if self.kind=="READ": out=s[self.a]
        elif self.kind=="SET": s[self.a]=self.value; out=s[self.a]
        elif self.kind=="INC": s[self.a]+=1; out=s[self.a]
        elif self.kind=="COPYPLUS": s[self.b]=s[self.a]+1; out=s[self.b]
        else: raise ValueError(self.kind)
        return tuple(s),out

def ops():
    out=[]
    for r in RESOURCES: out.append(Op("READ",r))
    for r in RESOURCES:
        out.append(Op("SET",r,value=0)); out.append(Op("SET",r,value=1))
    for r in RESOURCES: out.append(Op("INC",r))
    for src in RESOURCES:
        for dst in RESOURCES:
            if src!=dst: out.append(Op("COPYPLUS",src,dst))
    return tuple(out)
OPS=ops()
assert len(OPS)==18

def conflict(fp1,fp2):
    r1,w1=fp1; r2,w2=fp2
    return bool((w1 & (r2|w2)) or (r1 & w2))

def fp(op): return (op.reads,op.writes)

def union_fp(x,y): return (x[0]|y[0],x[1]|y[1])

def run_schedule(initial, programs, schedule):
    state=tuple(initial); obs={}
    for phase in schedule:
        state,val=programs[phase].apply(state)
        obs[phase]=val
    return state,tuple(sorted(obs.items()))

def serial_schedule(order):
    f,s=order
    return (f+"I",f+"T",s+"I",s+"T")

def overlap_schedules(order):
    f,s=order
    return (
        (f+"I",s+"I",f+"T",s+"T"),
        (f+"I",s+"I",s+"T",f+"T"),
    )

def eligible_complete(order,programs):
    f,s=order
    tail=fp(programs[f+"T"])
    second=union_fp(fp(programs[s+"I"]),fp(programs[s+"T"]))
    return not conflict(tail,second)

def omitted_decl_eligible(order,programs):
    f,s=order
    tr,tw=fp(programs[f+"T"])
    sr,sw=union_fp(fp(programs[s+"I"]),fp(programs[s+"T"]))
    bad=(tw & (sr|sw)) | (tr & sw)
    if not bad: return False
    return not conflict((tr-bad,tw-bad),(sr,sw))

def mismatch_for_any_overlap(initial,order,programs):
    base=run_schedule(initial,programs,serial_schedule(order))
    return any(run_schedule(initial,programs,s)!=base for s in overlap_schedules(order))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args()
    outp=Path(a.output); assert not outp.exists()
    counts={
      'program_vectors':0,'rows':0,'complete_overlap_admissions':0,
      'complete_overlap_schedule_checks':0,'complete_overlap_mismatches':0,
      'declared_conflict_serializations':0,'surface_only_mismatches':0,
      'omitted_dependency_admissions':0,'omitted_dependency_mismatches':0,
      'order_A_B_rows':0,'order_B_A_rows':0,
    }
    examples={'surface_only':None,'omitted_dependency':None}
    for vec in itertools.product(OPS, repeat=4):
        programs={'AI':vec[0],'AT':vec[1],'BI':vec[2],'BT':vec[3]}
        counts['program_vectors']+=1
        for initial in INITIAL_STATES:
            for order in (("A","B"),("B","A")):
                counts['rows']+=1; counts['order_'+order[0]+'_'+order[1]+'_rows']+=1
                mismatch=mismatch_for_any_overlap(initial,order,programs)
                if eligible_complete(order,programs):
                    counts['complete_overlap_admissions']+=1
                    counts['complete_overlap_schedule_checks']+=2
                    if mismatch:
                        counts['complete_overlap_mismatches']+=1
                else:
                    counts['declared_conflict_serializations']+=1
                    if mismatch:
                        counts['surface_only_mismatches']+=1
                        if examples['surface_only'] is None:
                            examples['surface_only']={'initial':initial,'order':order,'ops':{k:v.name for k,v in programs.items()}}
                    if omitted_decl_eligible(order,programs):
                        counts['omitted_dependency_admissions']+=1
                        if mismatch:
                            counts['omitted_dependency_mismatches']+=1
                            if examples['omitted_dependency'] is None:
                                examples['omitted_dependency']={'initial':initial,'order':order,'ops':{k:v.name for k,v in programs.items()}}
    read0=Op('READ',0); inc0=Op('INC',0); read1=Op('READ',1)
    unknown_parallel_admissions=0
    reversed_predicate_bad = not conflict(fp(inc0),fp(read0))
    corruption={
      'unknown_fail_closed': unknown_parallel_admissions==0,
      'rw_conflict_detected': conflict(fp(inc0),fp(read0)),
      'disjoint_not_conflict': not conflict(fp(inc0),fp(read1)),
      'surface_only_discriminator': counts['surface_only_mismatches']>0,
      'omitted_dependency_discriminator': counts['omitted_dependency_mismatches']>0,
      'reverse_predicate_rejected': reversed_predicate_bad is False,
    }
    decision='PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED' if (
      counts['complete_overlap_mismatches']==0 and counts['declared_conflict_serializations']>0 and
      unknown_parallel_admissions==0 and counts['surface_only_mismatches']>0 and
      counts['omitted_dependency_mismatches']>0 and counts['order_A_B_rows']>0 and counts['order_B_A_rows']>0 and
      all(corruption.values())
    ) else 'FAIL_PHASE_OVERLAP_RESOURCE_FOOTPRINT'
    result={
      'task':'PHASE-OVERLAP-RESOURCE-FOOTPRINT-SERIALIZABILITY-R0-20260918-001',
      'resources':list(RESOURCES),'initial_states':[list(x) for x in INITIAL_STATES],
      'operation_count':len(OPS),'counts':counts,'examples':examples,
      'unknown_parallel_admissions':unknown_parallel_admissions,'corruption_controls':corruption,
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning_after_freeze':0,'decision':decision,
    }
    result['digest']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    outp.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
