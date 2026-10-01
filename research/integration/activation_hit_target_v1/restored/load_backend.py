"""Load exact upstream bytes; omit only unused core-manifest import."""
import ast
import hashlib
from pathlib import Path
EXPECTED='9cae101a219348077668c8fc086acf8e13154afe'
def load():
    path=Path(__file__).with_name('backend.py'); data=path.read_bytes()
    actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    if actual!=EXPECTED: raise RuntimeError('STOP_UPSTREAM_SOURCE_MISMATCH')
    tree=ast.parse(data,filename=str(path))
    removed=[n for n in tree.body if isinstance(n,ast.ImportFrom) and n.module=='runtime.core_v1.contract']
    if len(removed)!=1: raise RuntimeError('unexpected import structure')
    tree.body=[n for n in tree.body if n not in removed]
    ns={'__name__':'isolated_backend','__file__':str(path)}
    exec(compile(tree,str(path),'exec'),ns)
    return ns['X11Backend']
