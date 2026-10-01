import json, queue, sys
from pathlib import Path

class SessionError(RuntimeError): pass

class Session:
    def __init__(self, retained=(), queued=()):
        self.events=list(retained)
        self.queue=queue.Queue()
        for r in queued: self.queue.put(dict(r))
        self.latest_exact={'event':'observation','sequence':7}
        self.sent=[]
    def send(self, cmd): self.sent.append(dict(cmd))
    def wait(self,predicate,*,replay=False):
        if replay:
            matches=[r for r in self.events if predicate(r)]
            if len(matches)>1: raise SessionError('ambiguous retained replay')
            if len(matches)==1: return matches[0]
        while not self.queue.empty():
            row=self.queue.get()
            if predicate(row): return row
        raise TimeoutError('session event timeout')

def submit_old(session, identifier):
    session.send({'op':'submit','id':identifier,'expected_sequence':session.latest_exact['sequence']})
    row=session.wait(lambda r:r.get('event') in {'accepted','rejected'})
    if row.get('event')!='accepted' or row.get('id')!=identifier:
        raise SessionError(f'program rejected: {row}')
    return row

def submit_corrected(session, identifier):
    session.send({'op':'submit','id':identifier,'expected_sequence':session.latest_exact['sequence']})
    row=session.wait(lambda r:r.get('event') in {'accepted','rejected'} and r.get('id')==identifier)
    if row.get('event')!='accepted' or row.get('id')!=identifier:
        raise SessionError(f'program rejected: {row}')
    return row

def outcome(fn, session, identifier='fallback'):
    try:
        row=fn(session,identifier)
        return {'status':'RETURN','event':row.get('event'),'id':row.get('id'),'remaining':list(session.queue.queue),'sent':session.sent}
    except Exception as e:
        return {'status':'ERROR','error_type':type(e).__name__,'error':str(e),'remaining':list(session.queue.queue),'sent':session.sent}

def terminal_outcome(retained, ident='fallback'):
    s=Session(retained=retained)
    pred=lambda r:r.get('event')=='terminal' and r.get('id')==ident
    try:
        r=s.wait(pred,replay=True)
        return {'status':'RETURN','id':r.get('id')}
    except Exception as e:
        return {'status':'ERROR','error_type':type(e).__name__,'error':str(e)}

def main(out):
    cases=[]
    submit_cases=[
      ('matching_accept',[{'event':'accepted','id':'fallback'}]),
      ('stale_accept_then_match',[{'event':'accepted','id':'prelude'},{'event':'accepted','id':'fallback'}]),
      ('stale_reject_then_match',[{'event':'rejected','id':'prelude'},{'event':'accepted','id':'fallback'}]),
      ('unrelated_then_match',[{'event':'clock','runtime_ns':1},{'event':'accepted','id':'fallback'}]),
      ('matching_reject',[{'event':'rejected','id':'fallback'}]),
      ('malformed_then_match',[{'foo':'bar'},{'event':'accepted','id':'fallback'}]),
    ]
    for name,rows in submit_cases:
        old=outcome(submit_old,Session(queued=rows))
        corrected=outcome(submit_corrected,Session(queued=rows))
        cases.append({'kind':'submit','name':name,'queue':rows,'old':old,'corrected':corrected})
    terminal_cases=[
      ('terminal_exact',[{'event':'terminal','id':'fallback'}]),
      ('terminal_duplicate',[{'event':'terminal','id':'fallback'},{'event':'terminal','id':'fallback'}]),
      ('terminal_wrong_id',[{'event':'terminal','id':'other'}]),
    ]
    for name,rows in terminal_cases:
        cases.append({'kind':'terminal','name':name,'retained':rows,'corrected':terminal_outcome(rows)})
    result={'schema':'issue3349-replay-identity-v2-raw','cases':cases,'case_count':len(cases)}
    Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__': main(sys.argv[1])
