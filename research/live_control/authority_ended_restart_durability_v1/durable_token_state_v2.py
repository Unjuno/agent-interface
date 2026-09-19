from __future__ import annotations
import json,os,uuid
from dataclasses import dataclass
from pathlib import Path
from authority_ended_bridge_v1 import to_caller_execution_decision
SCHEMA='authority-ended-durable-token-state-v2'
class StateError(ValueError):pass
class DuplicateReceipt(ValueError):pass
class TokenConsumed(ValueError):pass
class TokenMissing(ValueError):pass
class InjectedCrash(RuntimeError):pass
@dataclass
class Token:
    authority_end_id:str
    post_sequence:int

def _validate(obj):
    if type(obj) is not dict or obj.get('schema')!=SCHEMA:raise StateError('invalid durable token state schema')
    ent=obj.get('entries')
    if type(ent) is not dict:raise StateError('entries object required')
    out={}
    for rid,row in ent.items():
        if type(rid) is not str or not rid:raise StateError('nonempty authority_end_id required')
        if type(row) is not dict or type(row.get('post_sequence')) is not int or row.get('post_sequence')<1 or row.get('status') not in ('pending','consumed'):
            raise StateError('invalid durable token entry')
        out[rid]={'post_sequence':row['post_sequence'],'status':row['status']}
    return out

def _bytes(entries):return (json.dumps({'schema':SCHEMA,'entries':entries},sort_keys=True,separators=(',',':'))+'\n').encode()
class DurableTokenLedger:
    def __init__(self,path,*,initialize=False):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        if self.path.exists():
            try:self.entries=_validate(json.loads(self.path.read_text()))
            except StateError:raise
            except Exception as e:raise StateError('unreadable durable token state') from e
        elif initialize:
            self.entries={};self._persist(self.entries)
        else:raise StateError('durable token state missing')
    def _persist(self,entries,*,fault=None):
        tmp=self.path.parent/(self.path.name+'.tmp-'+uuid.uuid4().hex)
        fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            view=memoryview(_bytes(entries))
            while view:
                n=os.write(fd,view);view=view[n:]
            os.fsync(fd)
        finally:os.close(fd)
        if fault=='after_temp_fsync':raise InjectedCrash('after_temp_fsync')
        os.replace(tmp,self.path)
        dfd=os.open(self.path.parent,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
        try:os.fsync(dfd)
        finally:os.close(dfd)
        if fault=='after_replace_fsync':raise InjectedCrash('after_replace_fsync')
    def issue(self,receipt,*,fault=None):
        d=to_caller_execution_decision(receipt)
        if d != {'status':'safe_yield','reason':'authority_unavailable','completed_actions':receipt['steps_completed']}:raise ValueError('unexpected bridge decision')
        rid=receipt.get('authority_end_id'); seq=receipt['post_authority']['sequence']
        if type(rid) is not str or not rid:raise StateError('runtime authority_end_id required')
        if rid in self.entries:raise DuplicateReceipt('authority_end_id already exists')
        new={k:dict(v) for k,v in self.entries.items()};new[rid]={'post_sequence':seq,'status':'pending'}
        self._persist(new,fault=fault);self.entries=new;return Token(rid,seq)
    def recover_pending(self,rid):
        row=self.entries.get(rid)
        if row is None:raise TokenMissing('authority_end_id missing')
        if row['status']=='consumed':raise TokenConsumed('authority_end_id already consumed')
        return Token(rid,row['post_sequence'])
    def consume(self,token,*,fault=None):
        row=self.entries.get(token.authority_end_id)
        if row is None:raise TokenMissing('authority_end_id missing')
        if row['post_sequence']!=token.post_sequence:raise StateError('token post_sequence mismatch')
        if row['status']=='consumed':raise TokenConsumed('authority_end_id already consumed')
        new={k:dict(v) for k,v in self.entries.items()};new[token.authority_end_id]['status']='consumed'
        self._persist(new,fault=fault);self.entries=new
    def revalidate(self,token,current_sequence,*,association_changed=False):
        row=self.entries.get(token.authority_end_id)
        if row is None:return {'status':'token_missing'}
        if row['status']=='consumed':return {'status':'token_replay'}
        if type(current_sequence) is not int or current_sequence<=token.post_sequence:return {'status':'stale'}
        if association_changed:return {'status':'association_changed'}
        return {'status':'revalidated'}
