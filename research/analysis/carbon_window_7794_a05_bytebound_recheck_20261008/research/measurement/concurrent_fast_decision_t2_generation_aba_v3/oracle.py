# Independently structured history oracle; no import from candidate model.
class Oracle:
    def __init__(self):
        self.scope={}
        self.prepared={}
        self.effects=[]
    def req(self,s):
        x=self.scope.setdefault(s,{"gen":0,"open":False,"state":"HARD","returns":set()})
        x["gen"]+=1; x["open"]=True; return (True,x["gen"])
    def obs(self,s,state):
        if state not in ("CLEAR","WATCH","HARD"): return (False,"BAD_STATE")
        self.scope.setdefault(s,{"gen":0,"open":False,"state":"HARD","returns":set()})["state"]=state; return (True,None)
    def prep(self,s,d):
        if not d or d in self.prepared: return (False,"BAD_OR_DUP")
        x=self.scope.setdefault(s,{"gen":0,"open":False,"state":"HARD","returns":set()})
        if not x["open"]: return (False,"CLOSED")
        self.prepared[d]={"scope":s,"gen":x["gen"],"state":x["state"],"used":False}; return (True,x["gen"])
    def ret(self,s,e):
        x=self.scope.setdefault(s,{"gen":0,"open":False,"state":"HARD","returns":set()})
        if not e or e in x["returns"]: return (False,"DUP")
        x["returns"].add(e); x["open"]=False; return (True,x["gen"])
    def admit(self,s,d,auth,claimed=None):
        p=self.prepared.get(d)
        if p is None: return False
        if p["used"] or p["scope"]!=s: return False
        x=self.scope.setdefault(s,{"gen":0,"open":False,"state":"HARD","returns":set()})
        if claimed is not None and claimed != p["gen"]: return False
        good=bool(auth and x["open"] and x["state"]=="CLEAR" and p["state"]=="CLEAR" and p["gen"]==x["gen"])
        if good:
            p["used"]=True; self.effects.append((s,d,x["gen"]))
        return good
    def snapshot(self):
        return {
          "scope": {k:{"gen":v["gen"],"open":v["open"],"state":v["state"],"returns":sorted(v["returns"])} for k,v in sorted(self.scope.items())},
          "prepared": {k:dict(v) for k,v in sorted(self.prepared.items())},
          "effects": list(self.effects),
        }
