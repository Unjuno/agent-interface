"""Read-only retained engineering artifact check. No extraction or GUI replay."""
import ast,hashlib,json,re,tarfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parent

def need(ok,message):
    if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
manifest=json.loads((ROOT/'manifest.json').read_text())
need(sha((ROOT/'raw.tar.gz').read_bytes())==manifest['archive_sha256'],'archive digest')
files={}
with tarfile.open(ROOT/'raw.tar.gz','r:gz') as archive:
    for member in archive.getmembers():
        path=PurePosixPath(member.name)
        need(member.isfile() and not path.is_absolute() and '..' not in path.parts,'unsafe member')
        need(member.name not in files,'duplicate member')
        files[member.name]=archive.extractfile(member).read()
need(set(files)==set(manifest['files']),'member closure')
for name,data in files.items():
    entry=manifest['files'][name]
    need(len(data)==entry['bytes'] and sha(data)==entry['sha256'],'member bytes '+name)# Only the retained data-only auditor is evaluated; no measured runtime imports.
namespace={'__name__':'retained_stage_audit'}
exec(compile(files['audit.py'].decode('utf-8-sig'),'retained-stage-audit','exec'),namespace)
print(json.dumps(namespace['audit'](files),indent=2))
