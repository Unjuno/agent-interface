"""Construction-only gates: no optimizer step or evaluation allocation."""
import torch
from runner import Core,LoRA,dispatch,labels,EPOCH
def run():
 x=torch.tensor([[1.,1,0,0,0,0,0,0],[-1.,1,0,0,0,0,0,0],[1.,-1,0,0,0,0,0,0],[-1.,-1,0,0,0,0,0,0]])
 assert labels(x).tolist()==[3,1,2,0] and labels(x,True).tolist()==[1,3,0,2]
 base=Core();a=LoRA(base,2);b=LoRA(base,4)
 assert a.a.shape==(16,2) and b.a.shape==(16,4) and b.b.shape==(4,4)
 reg={"rank2_online":a,"rank4_online":b,"rank4_batch":b}
 assert dispatch("A",EPOCH,0,base,reg)==("PROPOSE",base)
 assert dispatch("rank4_online",EPOCH,16,base,reg)==("PROPOSE",b)
 assert dispatch("rank4_online",EPOCH-1,16,base,reg)[0]=="YIELD"
 assert dispatch("rank4_online",EPOCH,15,base,reg)[0]=="YIELD"
 assert dispatch("unknown",EPOCH,16,base,reg)[0]=="YIELD"
 assert dispatch("missing",EPOCH,16,base,reg)[0]=="YIELD"
 return "PASS_CONSTRUCTION_6"
if __name__=="__main__":print(run())
