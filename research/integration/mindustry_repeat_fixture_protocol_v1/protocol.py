class Protocol:
    def __init__(self, fixture):
        self.f=fixture; self.i=0; self.phase='ready'; self.events=[]; self.last_epoch=0
        self._ready()
    @property
    def task(self): return self.f['tasks'][self.i] if self.i < len(self.f['tasks']) else None
    def _emit(self,event,**kw): self.events.append(dict(event=event,**kw))
    def _ready(self):
        t=self.task
        if t is None: self.phase='complete'; self._emit('complete'); return
        self.phase='ready'; self._emit('task_ready',task_id=t['task_id'],layout=t['layout'],benchmark_epoch=t['epoch'])
    def controller(self,op):
        if op not in self.f['controller_ops']:
            self._emit('controller_rejected',op=op,reason='unsupported_controller_op'); return False
        self._emit('controller_command',op=op); return True
    def checkpoint(self,epoch):
        if self.phase!='ready' or self.task is None or epoch!=self.task['epoch'] or epoch<=self.last_epoch:
            self._emit('checkpoint_refused',epoch=epoch); return False
        self.phase='await_score'; self._emit('checkpoint_snapshot',epoch=epoch); return True
    def score(self,epoch,passed):
        if self.phase!='await_score' or self.task is None or epoch!=self.task['epoch']:
            self._emit('score_refused',epoch=epoch); return False
        if not passed:
            self.phase='stopped'; self._emit('task_failed',epoch=epoch); return False
        self.phase='await_reset'; self._emit('score_verified',epoch=epoch); return True
    def reset(self,epoch,witness_ok=True):
        if self.phase!='await_reset' or self.task is None or epoch!=self.task['epoch']:
            self._emit('reset_refused',epoch=epoch); return False
        self._emit('reset_applied',epoch=epoch,target=[137,52],copper='canonical')
        if not witness_ok:
            self.phase='stopped'; self._emit('reset_witness_failed',epoch=epoch); return False
        self._emit('reset_witness',epoch=epoch); self.last_epoch=epoch
        old=self.task
        self.i += 1
        if old['task_id']=='A3': self._emit('geometry_mutation',from_layout='A',to_layout='B')
        self._ready(); return True
    def force_ready(self):
        if self.phase!='ready': self._emit('ready_refused',reason='reset_witness_required'); return False
        self._ready(); return True

def controller_projection(events,fixture):
    allowed={'task_ready','controller_rejected','controller_command','complete'}
    out=[]
    for e in events:
        if e['event'] not in allowed: continue
        if e['event']=='task_ready':
            out.append({'event':'task_ready','task_id':e['task_id'],'task':'Place exactly one north-facing Conveyor in the empty tile directly above the copper item source, then finish paused with no pending build plans.','layout':e['layout'],'benchmark_epoch':e['benchmark_epoch']})
        else: out.append(dict(e))
    return out
