"""Read-only exact file-set custody across host/private guest."""
import hashlib
import re
from pathlib import Path
from runner import VM,receipt
import reference as ref

def assert_manifest(actual,expected,label):
    for mapping in (actual,expected):
        ref.need(type(mapping) is dict and bool(mapping),'nonempty manifest map')
        for name,digest in mapping.items():
            ref.need(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts,
                     'relative closed manifest path')
            ref.need(type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None,'exact hash syntax')
    ref.join(actual,expected,label)

def host_manifest(root):
    root=Path(root);ref.need(root.is_dir() and not root.is_symlink(),'real manifest root')
    result={}
    for p in sorted(root.rglob('*')):
        ref.need(not p.is_symlink(),'no custody symlink')
        if p.is_file():result[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    ref.need(bool(result),'nonempty custody tree')
    return result

def guest_manifest(root,receipt_sink=None):
    prefix=['orbctl','run','-m',VM];receipts=[]
    def recorded(command):
        value=receipt(command)
        receipts.append(value)
        if receipt_sink is not None:receipt_sink(len(receipts),value)
        return value
    links=recorded(prefix+['find',root,'-type','l','-print'])
    ref.need(ref.integer(links['exit_code'])==0 and not links['stdout'].strip(),'no guest custody symlink')
    files=recorded(prefix+['find',root,'-type','f','-print'])
    ref.need(ref.integer(files['exit_code'])==0,'guest file inventory')
    paths=sorted(files['stdout'].splitlines())
    ref.need(bool(paths) and len(paths)==len(set(paths)) and
             all(p.startswith(root+'/') for p in paths),'closed guest file inventory')
    hashes=recorded(prefix+['sha256sum']+paths)
    ref.need(ref.integer(hashes['exit_code'])==0,'guest whole-tree hashes')
    result={}
    for line in hashes['stdout'].splitlines():
        digest,path=line.split(maxsplit=1)
        ref.need(path in paths and path[len(root)+1:] not in result,'unique guest hash identity')
        result[path[len(root)+1:]]=digest
    ref.need(len(result)==len(paths),'complete guest hash denominator')
    return result,receipts
