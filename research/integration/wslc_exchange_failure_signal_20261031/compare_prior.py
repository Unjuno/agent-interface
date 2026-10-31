from pathlib import Path
from zipfile import ZipFile
import hashlib,json,subprocess,sys
here=Path(__file__).resolve().parent;prior=here.parent/'wslc_three_arm_lifecycle_first_newseed_20261031';path=prior/'public.zip';assert hashlib.sha256(path.read_bytes()).hexdigest()=='933ecb915ed55bd8646457158f82fa87c2e6d4a1e8f3acf11f50f7f9a43da88b'
for folder in (prior,here):assert json.loads(subprocess.check_output([sys.executable,str(folder/'audit.py')],text=True))['status']=='audited'
def last(archive,name):
 with ZipFile(archive) as z:
  row=json.loads(z.read(name))[-1]['adaptive']['attempt_ledger'][0]
  return {'seconds':(row['completed_ns']-row['started_ns'])/1e9,'error':row['error'],'usage':row['usage']}
a=last(path,'at03/out/arms/ephemeral/task-details.json');b=last(here/'public.zip','av01/out/arms/ephemeral/task-details.json');assert 'TimeoutError' in a['error'] and 'HostFailure' in b['error'] and a['usage'] is None and b['usage'] is None
print(json.dumps({'status':'audited','prior_uncontrolled':a,'successor_injected':b,'scope':'separate allocations, seed and fault conditions; descriptive only'},indent=2))
