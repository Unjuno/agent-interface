"""Construction-only checks; no optimizer step or held-out evaluation."""
def run_construction():
 assert SEEDS==(3461,3462,3463,3464,3465)
 x=data(4,3461)
 assert labels(x).shape==(4,) and labels(x,True).shape==(4,)
 base=Core();torch.manual_seed(99);template=LoRA(base,4);state=clone_state(template)
 torch.manual_seed(99);a=LoRA(base,4);a.load_state_dict(state)
 torch.manual_seed(99);b=LoRA(base,4);b.load_state_dict(state)
 assert a.a.shape==(16,4) and a.b.shape==(4,4) and state_equal(a,state) and state_equal(b,state)
 order,sched=make_schedule(3461)
 assert len(order)==16 and len(sched)==16 and all(len(s)==8 and all(len(batch)==32 for batch in s) for s in sched)
 registry={"B_R4_ONLINE_02":a}
 assert dispatch("B_R4_ONLINE_02",1,1,"rank4_02",1,1,base,registry)==("PROPOSE",a)
 assert dispatch("B_R4_ONLINE_02",0,1,"rank4_02",1,1,base,registry)[0]=="YIELD"
 assert dispatch("B_R4_ONLINE_02",1,1,"rank4_02",0,1,base,registry)[0]=="YIELD"
 assert dispatch("B_MISSING",1,1,"bad",1,1,base,registry)[0]=="YIELD"
 assert dispatch("B_R4_ONLINE_02",1,1,None,1,1,base,registry)[0]=="YIELD"
 assert dispatch("B_R4_ONLINE_02",1,1,"rank4_02",None,1,base,registry)[0]=="YIELD"
 assert dispatch("B_R4_ONLINE_02",None,1,"rank4_02",1,1,base,registry)[0]=="YIELD"
 return "PASS_CONSTRUCTION_9"
if __name__=="__main__":print(run_construction())
