"""Recorded action lifecycle; no input, lease creation, polling loop or automatic retry."""
import copy
import json


class PendingAction:
    def __init__(self, action_id, after):
        if not isinstance(action_id,str) or not 1<=len(action_id)<=128:
            raise ValueError('bounded action id required')
        if type(after) is not int or after<0:raise ValueError('cursor required')
        self.action_id=action_id;self.cursor=after;self.seen={}
        self.accepted=None;self.stopped=None;self.terminal=None;self.observation=None
        self.uncertainty=None

    def ingest(self, after, reply):
        try:
            if type(after) is not int or after<0 or after>self.cursor:
                raise ValueError('unexpected reply start')
            if reply.get('status') not in ('boundary','timeout','batch_limit','closed'):
                raise ValueError('unresolved transport status: '+str(reply.get('status')))
            records=reply.get('records');end=reply.get('cursor')
            if not isinstance(records,list) or type(end) is not int or end!=after+len(records):
                raise ValueError('noncontiguous reply')
            if len(self.seen)+max(0,end-self.cursor)>4096:raise ValueError('action history limit')
            # Validate overlap before applying any new event.
            for i,e in enumerate(records,after+1):
                encoded=json.dumps(e,sort_keys=True,separators=(',',':'),allow_nan=False)
                if i<=self.cursor and self.seen.get(i)!=encoded:
                    raise ValueError('conflicting or unavailable replay')
            for i,e in enumerate(records,after+1):
                if i<=self.cursor:continue
                self.seen[i]=json.dumps(e,sort_keys=True,separators=(',',':'),allow_nan=False)
                self.cursor=i
                if e.get('event')=='rejected':raise ValueError('unattributed runtime rejection')
                name=e.get('event')
                if name not in ('accepted','input_stopped','terminal','observation'):continue
                if not isinstance(e.get('id'),str) or not e['id']:raise ValueError('event identity missing')
                if e['id']!=self.action_id:continue
                if name=='accepted':
                    if self.accepted is not None:raise ValueError('duplicate admission')
                    self.accepted=copy.deepcopy(e)
                elif name=='observation':
                    if self.terminal is not None:raise ValueError('observation after terminal')
                    self.observation=copy.deepcopy(e)
                else:
                    if self.accepted is None:raise ValueError('outcome without recorded admission')
                    if self.terminal is not None:raise ValueError('outcome after terminal')
                    release=e.get('release',{})
                    if release.get('verified') is not True or release.get('keys_down')!=[] or release.get('buttons_down')!=[]:
                        raise ValueError('input release not established')
                    if name=='input_stopped':
                        if self.stopped is not None:raise ValueError('duplicate stopped event')
                        if e.get('decision_reason') not in ('focus_changed','surface_changed'):
                            raise ValueError('unknown stop reason')
                        self.stopped=copy.deepcopy(e)
                    else:
                        if e.get('status') not in ('completed','failed','expired','cancelled','needs_decision'):
                            raise ValueError('unknown terminal status')
                        if self.stopped is not None and (e.get('interruption')!=self.stopped.get('interruption') or
                            e.get('decision_reason')!=self.stopped.get('decision_reason') or e.get('status')!='needs_decision'):
                            raise ValueError('terminal conflicts with stop evidence')
                        self.terminal=copy.deepcopy(e)
            if reply['status']=='closed' and self.terminal is None:
                raise ValueError('stream closed before terminal')
        except (ValueError,TypeError,AttributeError) as exc:
            if self.uncertainty is None:self.uncertainty=str(exc)
        return self.view()

    def view(self):
        state=('needs_reconciliation' if self.uncertainty else 'terminal_received' if self.terminal else
               'input_stopped_capture_pending' if self.stopped else 'awaiting_outcome')
        return dict(state=state,action_id=self.action_id,cursor=self.cursor,
            uncertainty=self.uncertainty,stopped=copy.deepcopy(self.stopped),terminal=copy.deepcopy(self.terminal),
            observation=copy.deepcopy(self.observation),input_authority='none',
            meaning='Historical action state; terminal is not task success or permission to reuse a lease.')

    def poll_request(self, timeout=1):
        if self.uncertainty or self.terminal is not None:raise ValueError('no pending poll')
        if type(timeout) not in (int,float) or not 0<=timeout<=30:raise ValueError('timeout 0..30')
        return dict(after=self.cursor,events=['input_stopped','terminal'] if self.stopped is None else ['terminal'],
                    action_id=self.action_id,timeout=timeout)
