"""Reconstruct the explicit research candidate in a NEW private directory."""
import hashlib, json, shutil, sys
from pathlib import Path

def prepare(root):
    root=Path(root); baseline=root/'current_source';candidate=root/'candidate_source'
    freeze=json.loads((root/'FREEZE.json').read_text())
    if candidate.exists(): raise FileExistsError('candidate destination already exists')
    for rel,digest in freeze['files'].items():
        if rel.startswith('current_source/'):
            if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest: raise ValueError('baseline mismatch')
    shutil.copytree(baseline,candidate)
    file=candidate/'runtime/backends/x11_v1/backend.py'
    old='''    def text(self, value: str) -> None:
        # Resolve the entire supported payload before emitting its first key.
        for keys in self._text_plan(value):
            self.key_chord(keys)
'''
    new='''    def text(self, value: str) -> None:
        # Research candidate k8n4: this query is not atomic with later input.
        plan = self._text_plan(value)
        if value and self.root.query_pointer().mask & X.LockMask:
            raise X11BackendError("CAPS_LOCK_ACTIVE: literal text refused; lock unchanged")
        for keys in plan:
            self.key_chord(keys)
'''
    data=file.read_text();assert data.count(old)==1;file.write_text(data.replace(old,new))
    for rel,digest in freeze['files'].items():
        if rel.startswith('candidate_source/'):
            if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest: raise ValueError('candidate mismatch')
if __name__=='__main__':prepare(sys.argv[1])
