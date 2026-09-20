import importlib.util, json, queue, sys
from pathlib import Path

src=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('candidate_runner',src)
mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)

def make(rows=(),queued=()):
 s=mod.JsonSession.__new__(mod.JsonSession); s.events=list(rows); s.queue=queue.Queue(); s.process=type('P',(),{'poll':lambda self:None})()
 for x in queued:s.queue.put(x)
 return s
def wait_ok(s,p,**kw):
 try:return s.wait(p,timeout=.01,**kw)
 except TypeError:return None
def must_timeout(s,p,**kw):
 try:s.wait(p,timeout=.01,**kw)
 except (TimeoutError,mod.SessionError,TypeError):return True
 return False
term=lambda r:r.get('event')=='terminal' and r.get('id')=='fallback'
out={}
# Matching terminal is replayable only when cleanup explicitly requests replay.
v=wait_ok(make([{'event':'terminal','id':'fallback'}]),term,replay=True);out['terminal_opt_in']=isinstance(v,dict) and v.get('id')=='fallback'
out['terminal_default_isolated']=must_timeout(make([{'event':'terminal','id':'fallback'}]),term)
# Stale accepted/rejected rows must not satisfy queue-bound submit waits.
for name,event in [('stale_accept','accepted'),('stale_reject','rejected')]:
 row={'event':event,'id':'prelude'}
 out[name+'_cannot_satisfy_submit']=must_timeout(make([row]),lambda r:r.get('id')=='fallback')
# Duplicate matching terminal evidence is ambiguous and fails closed.
out['duplicate_terminal_rejected']=must_timeout(make([{'event':'terminal','id':'fallback'},{'event':'terminal','id':'fallback'}]),term,replay=True)
out['wrong_terminal_id_rejected']=must_timeout(make([{'event':'terminal','id':'other'}]),term,replay=True)
valid={'event':'accepted','id':'fallback'}
v=wait_ok(make([], [valid]),lambda r:r.get('id')=='fallback');out['queued_fallback_accepted']=isinstance(v,dict) and v.get('id')=='fallback'
v=wait_ok(make([{'event':'accepted','id':'prelude'}],[{'event':'accepted','id':'prelude'},valid]),lambda r:r.get('id')=='fallback');out['stale_then_queued_fallback_accepted']=isinstance(v,dict) and v.get('id')=='fallback'
print(json.dumps(out,sort_keys=True))
sys.exit(0 if all(out.values()) else 1)
