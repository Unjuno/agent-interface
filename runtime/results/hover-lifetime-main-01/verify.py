import hashlib,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
def require(value,message):
 if not value:raise ValueError(message)
result=json.loads((root/'result.json').read_text());manifest=json.loads((root/'raw-manifest.json').read_text())
require(hashlib.sha256((root/'raw.tar.gz').read_bytes()).hexdigest()==result['archive_sha256'],'archive')
require(hashlib.sha256((root/'audit.py').read_bytes()).hexdigest()==result['audit_sha256'],'auditor')
with tempfile.TemporaryDirectory() as directory,tarfile.open(root/'raw.tar.gz','r:gz') as archive:
 target=Path(directory);members=archive.getmembers()
 require(len(members)==len(manifest)==result['raw_files'],'inventory')
 for member in members:
  require(member.isfile() and member.name in manifest and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts,'member')
  data=archive.extractfile(member).read();expected=manifest[member.name]
  require(len(data)==expected['bytes'] and hashlib.sha256(data).hexdigest()==expected['sha256'],'member bytes')
  dest=target/member.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 command=[sys.executable]+(['-O'] if sys.flags.optimize else [])+[str(root/'audit.py'),str(target)]
 run=subprocess.run(command,capture_output=True)
 require(run.returncode==0,run.stderr.decode());fresh=json.loads(run.stdout)
 for key,value in fresh.items():require(result[key]==value,'result '+key)
 print('PASS personal hover, old-reference no-input refusal, exact images, finite lifetimes, one independent save and native suites. No speed or token claim.')
