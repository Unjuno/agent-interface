from __future__ import annotations
import hashlib,importlib.util,json,os,uuid
from pathlib import Path
import durable_token_state_v2 as base

PIN_SCHEMA='authority-ended-validator-source-pin-v2'
class ValidatorPinError(ValueError): pass
class InjectedInitCrash(RuntimeError): pass

def _bounded_id(value):
    if type(value) is not str or not value or len(value)>128: raise ValidatorPinError('bounded nonempty validator_id required')

def _load_validator(source,function_name):
    p=Path(source)
    try: data=p.read_bytes()
    except Exception as e: raise ValidatorPinError('validator source unreadable') from e
    sha=hashlib.sha256(data).hexdigest()
    if type(function_name) is not str or not function_name or len(function_name)>128: raise ValidatorPinError('bounded validator function name required')
    spec=importlib.util.spec_from_file_location('_authority_validator_'+sha[:16],p)
    if spec is None or spec.loader is None: raise ValidatorPinError('validator source not loadable')
    mod=importlib.util.module_from_spec(spec)
    try: spec.loader.exec_module(mod)
    except Exception as e: raise ValidatorPinError('validator source import failed') from e
    fn=getattr(mod,function_name,None)
    if not callable(fn): raise ValidatorPinError('validator callable missing')
    return sha,fn

def _meta(validator_id,sha,function_name):
    return {'schema':PIN_SCHEMA,'validator_id':validator_id,'validator_sha256':sha,'function_name':function_name}

def _load_pin(path):
    try: obj=json.loads(Path(path).read_text())
    except Exception as e: raise ValidatorPinError('unreadable validator pin') from e
    if type(obj) is not dict or set(obj)!={'schema','validator_id','validator_sha256','function_name'} or obj.get('schema')!=PIN_SCHEMA:
        raise ValidatorPinError('invalid validator pin schema')
    _bounded_id(obj.get('validator_id'))
    sha=obj.get('validator_sha256')
    if type(sha) is not str or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha): raise ValidatorPinError('invalid validator sha256')
    if type(obj.get('function_name')) is not str or not obj['function_name']: raise ValidatorPinError('invalid validator function name')
    return obj

def _persist_pin(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.parent/(path.name+'.tmp-'+uuid.uuid4().hex)
    fd=os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        view=memoryview((json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode())
        while view:
            n=os.write(fd,view);view=view[n:]
        os.fsync(fd)
    finally: os.close(fd)
    os.replace(tmp,path);dfd=os.open(path.parent,os.O_RDONLY|getattr(os,'O_DIRECTORY',0))
    try: os.fsync(dfd)
    finally: os.close(dfd)

class SourcePinnedValidatorLedger:
    def __init__(self,path,*,validator_id,validator_source,function_name='to_caller_execution_decision',initialize=False,fault=None):
        _bounded_id(validator_id);sha,validator=_load_validator(validator_source,function_name)
        self.path=Path(path);self.pin_path=Path(str(self.path)+'.validator.json');self.validator_id=validator_id;self.validator_sha256=sha;self.function_name=function_name;self.validator=validator
        state_exists=self.path.exists();pin_exists=self.pin_path.exists();expected=_meta(validator_id,sha,function_name)
        if state_exists and not pin_exists: raise ValidatorPinError('existing token state missing validator pin')
        if pin_exists:
            if _load_pin(self.pin_path)!=expected: raise ValidatorPinError('validator pin mismatch')
        else:
            if not initialize: raise ValidatorPinError('validator pin missing')
            _persist_pin(self.pin_path,expected)
            if fault=='after_sidecar': raise InjectedInitCrash('after_sidecar')
        if self.path.exists(): self.inner=base.DurableTokenLedger(self.path)
        elif initialize: self.inner=base.DurableTokenLedger(self.path,initialize=True)
        else: raise base.StateError('durable token state missing')
    @property
    def entries(self):return self.inner.entries
    def issue(self,receipt,*,fault=None):
        d=self.validator(receipt)
        if d!={'status':'safe_yield','reason':'authority_unavailable','completed_actions':receipt['steps_completed']}:raise ValueError('unexpected validator decision')
        rid=receipt.get('authority_end_id');seq=receipt['post_authority']['sequence']
        if type(rid) is not str or not rid:raise base.StateError('runtime authority_end_id required')
        if rid in self.inner.entries:raise base.DuplicateReceipt('authority_end_id already exists')
        new={k:dict(v) for k,v in self.inner.entries.items()};new[rid]={'post_sequence':seq,'status':'pending'}
        self.inner._persist(new,fault=fault);self.inner.entries=new;return base.Token(rid,seq)
    def recover_pending(self,rid):return self.inner.recover_pending(rid)
    def consume(self,token,*,fault=None):return self.inner.consume(token,fault=fault)
    def revalidate(self,token,current_sequence,*,association_changed=False):return self.inner.revalidate(token,current_sequence,association_changed=association_changed)
