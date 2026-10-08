"""A09 preparation: bounded private-pipe transport and admission boundary."""
import json
import os
import re
import time
import hashlib


class PipeWriteError(RuntimeError):
    def __init__(self,trace):
        self.trace=trace
        super().__init__('short private-pipe write')


def write_once(fd,value,write=os.write,clock=time.monotonic_ns):
    frame=encode_frame(value)
    trace={'started_ns':clock(),'requested_bytes':len(frame),'written_bytes':None,
           'sha256':hashlib.sha256(frame).hexdigest(),'frame_utf8':frame.decode('utf-8'),
           'write_error':None}
    try:
        trace['written_bytes']=write(fd,frame)
    except OSError as error:
        trace['write_error']=type(error).__name__+':'+str(error)
        trace['completed_ns']=clock()
        raise PipeWriteError(trace) from error
    trace['completed_ns']=clock()
    if type(trace['written_bytes']) is not int or trace['written_bytes']!=len(frame):
        raise PipeWriteError(trace)
    return trace


def unique_object(pairs):
    result={}
    for name,value in pairs:
        if name in result:raise ValueError('duplicate JSON key')
        result[name]=value
    return result


def reject_constant(value):
    raise ValueError('nonfinite JSON constant:'+value)


def encode_frame(value,max_bytes=512):
    if not isinstance(value,dict) or type(max_bytes) is not int or max_bytes<=0:
        raise ValueError('invalid frame or bound')
    frame=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
    if len(frame)>max_bytes:raise ValueError('frame byte budget exceeded')
    return frame


class FrameDecoder:
    def __init__(self,max_bytes=512,max_total_bytes=16384):
        if any(type(value) is not int or value<=0 for value in (max_bytes,max_total_bytes)):
            raise ValueError('invalid decoder bounds')
        self.max_bytes=max_bytes
        self.max_total_bytes=max_total_bytes
        self.buffer=b''
        self.total_bytes=0
        self.terminal=False

    def feed(self,chunk):
        if self.terminal:raise ValueError('terminal frame stream')
        try:return self._feed(chunk)
        except ValueError:
            self.terminal=True
            raise

    def _feed(self,chunk):
        if not isinstance(chunk,bytes):raise ValueError('byte frames required')
        self.total_bytes+=len(chunk)
        if self.total_bytes>self.max_total_bytes:raise ValueError('total byte budget exceeded')
        self.buffer+=chunk
        values=[]
        while b'\n' in self.buffer:
            line,self.buffer=self.buffer.split(b'\n',1)
            if len(line)+1>self.max_bytes:raise ValueError('frame byte budget exceeded')
            value=json.loads(line.decode('utf-8'),object_pairs_hook=unique_object,
                             parse_constant=reject_constant)
            if not isinstance(value,dict):raise ValueError('object frame required')
            values.append(value)
        if len(self.buffer)>=self.max_bytes:raise ValueError('unfinished frame byte budget exceeded')
        return values

    def finish(self):
        self.terminal=True
        if self.buffer:raise ValueError('partial frame at EOF')
        return None


def admission_errors(receipt,binding,seen_ns,click_started_ns,max_age_ns=50_000_000):
    errors=[]
    try:
        if (receipt.get('schema')!='issue5260-a09-focus-pipe-v1' or
                any(receipt.get(name)!=binding[name] for name in ('token','pid','target_id','freeze_sha256'))):
            errors.append('source_binding')
        if (not isinstance(binding['token'],str) or not binding['token'] or
                not isinstance(binding['freeze_sha256'],str) or
                not re.fullmatch(r'[a-f0-9]{64}',binding['freeze_sha256'])):
            errors.append('binding_format')
        typed=[receipt.get(name) for name in ('pid','target_id','sequence','event_ns','written_ns')]
        typed+=[binding['pid'],binding['target_id'],seen_ns,click_started_ns,max_age_ns]
        if any(type(value) is not int or value<=0 for value in typed):
            return errors+['receipt_types']
        if (receipt.get('kind')!='FocusIn' or receipt.get('widget')!='target' or
                receipt.get('focus_get')!='target'):
            errors.append('not_current_target')
        if not click_started_ns<=receipt['event_ns']<=receipt['written_ns']<=seen_ns:
            errors.append('receipt_clock_order')
        if seen_ns-receipt['written_ns']>max_age_ns:
            errors.append('receipt_expired')
    except (KeyError,TypeError,AttributeError):
        errors.append('malformed_receipt')
    return errors
