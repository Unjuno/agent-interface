"""Executor child whose key operations are brokered to a persistent owner."""
import json,socket,sys,threading,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from executor_v3 import Executor
class OwnerRPC:
    def __init__(self,fd):
        self.s=socket.socket(fileno=fd); self.r=self.s.makefile('r'); self.w=self.s.makefile('w'); self.lock=threading.Lock(); self.seq=0
    def call(self,op,key):
        with self.lock:
            self.seq+=1; n=self.seq; self.w.write(json.dumps({'id':n,'op':op,'key':key})+'\n'); self.w.flush(); ans=json.loads(self.r.readline())
            if ans.get('id')!=n or not ans.get('ok'): raise RuntimeError('owner RPC failed '+repr(ans))
            return ans.get('result')
class Sink:
    def __init__(self): self.lock=threading.Lock()
    def emit(self,row):
        with self.lock: print(json.dumps(row,sort_keys=True),flush=True)
class Backend:
    sequence=2
    def __init__(self,rpc,sink): self.rpc=rpc; self.sink=sink; self.down=[]
    def validate(self,steps):
        if steps != [{'op':'hold','keys':['a'],'duration_ms':5000}]: raise ValueError('unexpected hold')
    def execute(self,step,cancel,identifier,index):
        self.rpc.call('down','a'); self.down.append('a'); self.sink.emit({'event':'key_down_active','key':'a','at_ns':time.perf_counter_ns()})
        while not cancel.wait(.01): pass
    def release_all(self):
        if self.down: self.rpc.call('up_batch',self.down); self.down.clear()
        return {'verified':not self.down,'keys_down':list(self.down),'buttons_down':[],'owner_transitions':[]}
def main():
    rpc=OwnerRPC(int(sys.argv[1])); sink=Sink(); ex=Executor(Backend(rpc,sink),sink.emit)
    ex.submit('executor-crash-a02',[{'op':'hold','keys':['a'],'duration_ms':5000}],2,time.perf_counter_ns()+10_000_000_000)
    while True: time.sleep(1)
if __name__=='__main__': main()
