"""Archive bounded source bytes before sampling; preserve v1 worker semantics."""
import hashlib,time
from pathlib import Path
from effect_checkpoint import Checkpoints as Previous, sample


def archived_sample(path,contract,archive):
    started=time.perf_counter_ns()
    try:
        limit=65536 if contract['kind']=='saved_form_value' else 8*1024*1024
        with Path(path).open('rb') as stream:data=stream.read(limit+1)
        captured=time.perf_counter_ns()
        if len(data)>limit:raise ValueError('checkpoint source exceeds archive sample limit')
        digest=hashlib.sha256(data).hexdigest()
        archive=Path(archive);archive.mkdir(parents=True,exist_ok=True)
        snapshot=archive/(digest+'.bin')
        if snapshot.exists():
            if snapshot.read_bytes()!=data:raise ValueError('archive content mismatch')
        else:
            # One worker per runtime. This is a bounded research archive, not a durable journal.
            total=sum(p.stat().st_size for p in archive.glob('*.bin'))
            if total+len(data)>128*1024*1024:raise ValueError('checkpoint archive byte budget exceeded')
            with snapshot.open('xb') as target:target.write(data)
        evidence=sample(snapshot,contract)
        if evidence.get('artifact_sha256')!=digest:raise ValueError('sample/archive digest mismatch')
        evidence.update(archive_path=str(snapshot.resolve()),source_sampled_ns=captured,
            archive_source_path=str(path),archive_started_ns=started,archive_bytes=len(data),
            archive_scope='parsed archived bytes; original read not atomic; no durability or actor attribution')
        return evidence
    except Exception as exc:
        return dict(status='UNKNOWN',task_success=None,authority='none',attribution='not_established',
            observation_closed=False,contract=contract,reason='archive_or_evidence_unavailable',
            started_ns=started,finished_ns=time.perf_counter_ns(),error=dict(type=type(exc).__name__,message=str(exc)))


class Checkpoints(Previous):
    def __init__(self,emit,archive):
        super().__init__(emit);self.archive=Path(archive)
    def request(self,path,contract,metadata,verifier=None):
        return super().request(path,contract,metadata,
            verifier or (lambda path,contract:archived_sample(path,contract,self.archive)))
