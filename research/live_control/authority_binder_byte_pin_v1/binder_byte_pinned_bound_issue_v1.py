from __future__ import annotations
import hashlib,json,os,sys,types,uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
for p in [
    ROOT/'authority_ended_validator_byte_binding_v3',
    ROOT/'authority_ended_restart_durability_v1',
]:
    if str(p) not in sys.path:
        sys.path.insert(0,str(p))

from validator_byte_pinned_ledger_v3 import BytePinnedValidatorLedger

PIN_SCHEMA='authority-end-identity-binder-byte-pin-v1'
class BinderPinError(ValueError): pass
class InjectedBinderInitCrash(RuntimeError): pass

def _bounded_id(value):
    if type(value) is not str or not value or len(value)>128:
        raise BinderPinError('bounded nonempty binder_id required')

def _load_binder(source,function_name):
    p=Path(source)
    try:
        data=p.read_bytes()
    except Exception as e:
        raise BinderPinError('binder source unreadable') from e
    sha=hashlib.sha256(data).hexdigest()
    if type(function_name) is not str or not function_name or len(function_name)>128:
        raise BinderPinError('bounded binder function name required')
    try:
        code=compile(data,str(p),'exec',dont_inherit=True)
        mod=types.ModuleType('_authority_identity_binder_'+sha[:16])
        mod.__file__=str(p)
        exec(code,mod.__dict__)
    except Exception as e:
        raise BinderPinError('binder source execution failed') from e
    fn=getattr(mod,function_name,None)
    if not callable(fn):
        raise BinderPinError('binder callable missing')
    return sha,fn

def _meta(binder_id,sha,function_name):
    return {
        'schema':PIN_SCHEMA,
        'binder_id':binder_id,
        'binder_sha256':sha,
        'function_name':function_name,
    }

def _load_pin(path):
    try:
        obj=json.loads(Path(path).read_text())
    except Exception as e:
        raise BinderPinError('unreadable binder pin') from e
    if type(obj) is not dict or set(obj)!={'schema','binder_id','binder_sha256','function_name'} or obj.get('schema')!=PIN_SCHEMA:
        raise BinderPinError('invalid binder pin schema')
    _bounded_id(obj.get('binder_id'))
    sha=obj.get('binder_sha256')
    if type(sha) is not str or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
        raise BinderPinError('invalid binder sha256')
    if type(obj.get('function_name')) is not str or not obj['function_name'] or len(obj['function_name'])>128:
        raise BinderPinError('invalid binder function name')
    return obj

def _persist_pin(path,obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.parent/(path.name+'.tmp-'+uuid.uuid4().hex)
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        view=memoryview((json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode())
        while view:
            n=os.write(fd,view)
            view=view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp,path)
    dfd=os.open(path.parent,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)

class BinderBytePinnedBoundIssueLedger:
    def __init__(self,path,*,binder_id,binder_source,binder_function_name='bind_authority_end_identity',validator_id,validator_source,validator_function_name='to_caller_execution_decision',initialize=False,fault=None):
        _bounded_id(binder_id)
        binder_sha,binder=_load_binder(binder_source,binder_function_name)
        self.path=Path(path)
        self.binder_pin_path=Path(str(self.path)+'.binder.json')
        self.binder_id=binder_id
        self.binder_sha256=binder_sha
        self.binder_function_name=binder_function_name
        self.binder=binder
        expected=_meta(binder_id,binder_sha,binder_function_name)
        state_exists=self.path.exists()
        pin_exists=self.binder_pin_path.exists()
        if state_exists and not pin_exists:
            raise BinderPinError('existing token state missing binder pin')
        if pin_exists:
            if _load_pin(self.binder_pin_path)!=expected:
                raise BinderPinError('binder pin mismatch')
        else:
            if not initialize:
                raise BinderPinError('binder pin missing')
            _persist_pin(self.binder_pin_path,expected)
            if fault=='after_binder_sidecar':
                raise InjectedBinderInitCrash('after_binder_sidecar')
        inner_fault=None if fault=='after_binder_sidecar' else fault
        self._inner=BytePinnedValidatorLedger(
            self.path,
            validator_id=validator_id,
            validator_source=validator_source,
            function_name=validator_function_name,
            initialize=initialize,
            fault=inner_fault,
        )

    @property
    def entries(self):
        return self._inner.entries

    @property
    def validator_sha256(self):
        return self._inner.validator_sha256

    def issue(self,receipt,terminal,*,fault=None):
        bound=self.binder(receipt,terminal)
        return self._inner.issue(bound,fault=fault)

    def recover_pending(self,rid):
        return self._inner.recover_pending(rid)

    def consume(self,token,*,fault=None):
        return self._inner.consume(token,fault=fault)

    def revalidate(self,token,current_sequence,*,association_changed=False):
        return self._inner.revalidate(token,current_sequence,association_changed=association_changed)
