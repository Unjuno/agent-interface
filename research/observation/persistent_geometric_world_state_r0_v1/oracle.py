class HistoryOracle:
    def __init__(self, entities=16):
        self.generation={i:0 for i in range(entities)}
        self.events={i:[] for i in range(entities)}
    def observe(self,e,epoch,box):
        self.events[e].append(("OBSERVED",self.generation[e],epoch,tuple(box)))
    def infer(self,e,epoch,box):
        self.events[e].append(("INFERRED",self.generation[e],epoch,tuple(box)))
    def occlude(self,e,epoch):
        self.events[e].append(("UNKNOWN",self.generation[e],epoch,None))
    def advance_generation(self,e):
        self.generation[e]+=1
        self.events[e].append(("GENERATION",self.generation[e],None,None))
    def compact(self): pass
    def query_current(self,e):
        g=self.generation[e]
        for role,eg,epoch,box in reversed(self.events[e]):
            if role=="GENERATION":
                if eg==g: break
                continue
            if eg!=g: continue
            if role=="OBSERVED":
                return ("CURRENT_OBSERVED",box,epoch,g)
            return ("UNKNOWN",role)
        return ("UNKNOWN","NO_FACT_OR_STALE")
