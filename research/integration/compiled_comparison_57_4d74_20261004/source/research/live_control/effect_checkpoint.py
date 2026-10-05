"""One asynchronous artifact sample; no admission changes or action attribution."""
import hashlib,json,threading,time,urllib.parse
from pathlib import Path
from saved_effect import inspect_saved_cells


def sample(path, contract):
    result=dict(status='UNKNOWN',authority='none',attribution='not_established',
        task_success=None,observation_closed=False,contract=contract,started_ns=time.perf_counter_ns())
    try:
        if contract['kind']=='saved_cells':
            evidence=inspect_saved_cells(path,action_id='checkpoint-sample',expected=contract['expected'],observation_closed=False)
            for key in ('event','action_id'):evidence.pop(key,None)
            result.update(evidence)
        elif contract['kind']=='saved_form_value':
            with Path(path).open('rb') as stream:data=stream.read(65537)
            if len(data)>65536:raise ValueError('artifact exceeds 64 KiB sample limit')
            result['sampled_ns']=time.perf_counter_ns()
            result['artifact_sha256']=hashlib.sha256(data).hexdigest()
            actual=urllib.parse.parse_qs(data.decode('utf-8'),keep_blank_values=True,strict_parsing=True)
            result.update(actual=actual,scope='one saved form artifact, exact field mapping')
            if actual=={'value':[contract['expected']]}:
                result.update(status='VERIFIED',reason='sample_matches_declared_value')
            else:result['reason']='sample_mismatch_window_open'
        else:raise ValueError('unsupported contract')
    except Exception as exc:
        result.update(status='UNKNOWN',reason='evidence_unavailable',error=dict(type=type(exc).__name__,message=str(exc)))
    result['finished_ns']=time.perf_counter_ns()
    return result


class Checkpoints:
    def __init__(self,emit):
        self.emit=emit;self.lock=threading.Lock();self.busy=False;self.closed=False
    def request(self,path,contract,metadata,verifier=sample):
        # Snapshot caller-owned objects before returning to the command reader.
        contract=json.loads(json.dumps(contract,allow_nan=False));metadata=dict(metadata)
        with self.lock:
            if self.closed:raise ValueError('checkpoint service closed')
            if self.busy:
                self.emit(dict(event='effect_checkpoint',status='UNKNOWN',reason='verifier_busy',
                    task_success=None,authority='none',**metadata));return
            self.busy=True
        def work():
            try:
                try:evidence=verifier(path,contract)
                except Exception as exc:evidence=dict(status='UNKNOWN',reason='verifier_failed',error=type(exc).__name__)
                with self.lock:
                    if not self.closed:
                        self.emit(dict(event='effect_checkpoint',evidence=evidence,task_success=None,
                            authority='none',scope='non-final artifact query; input admission unchanged',**metadata))
            finally:
                with self.lock:self.busy=False
        threading.Thread(target=work,daemon=True).start()
    def close(self):
        with self.lock:self.closed=True
