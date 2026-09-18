from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Fact:
    role: str
    generation: int
    epoch: int
    box: Optional[tuple[int,int,int,int]]

class TypedWorldState:
    def __init__(self, entities=16):
        self.generation={i:0 for i in range(entities)}
        self.fact={}
        self.context_payload={}
    def observe(self,e,epoch,box):
        self.fact[e]=Fact("OBSERVED",self.generation[e],epoch,tuple(box))
        self.context_payload[(e,epoch)]="SOURCE"
    def infer(self,e,epoch,box):
        self.fact[e]=Fact("INFERRED",self.generation[e],epoch,tuple(box))
        self.context_payload[(e,epoch)]="PREDICTION"
    def occlude(self,e,epoch):
        self.fact[e]=Fact("UNKNOWN",self.generation[e],epoch,None)
    def advance_generation(self,e):
        self.generation[e]+=1
    def compact(self):
        self.context_payload.clear()
    def query_current(self,e):
        f=self.fact.get(e)
        if f is None:
            return ("UNKNOWN","NO_FACT")
        if f.generation!=self.generation[e]:
            return ("UNKNOWN","STALE_GENERATION")
        if f.role!="OBSERVED":
            return ("UNKNOWN",f.role)
        return ("CURRENT_OBSERVED",f.box,f.epoch,f.generation)

class LatestGeometryOnly:
    def __init__(self, entities=16):
        self.box={}
        self.generation={i:0 for i in range(entities)}
    def observe(self,e,epoch,box): self.box[e]=tuple(box)
    def infer(self,e,epoch,box): self.box[e]=tuple(box)
    def occlude(self,e,epoch): pass
    def advance_generation(self,e): self.generation[e]+=1
    def compact(self): pass
    def query_current(self,e):
        if e not in self.box: return ("UNKNOWN","NO_FACT")
        return ("CURRENT_OBSERVED",self.box[e])
