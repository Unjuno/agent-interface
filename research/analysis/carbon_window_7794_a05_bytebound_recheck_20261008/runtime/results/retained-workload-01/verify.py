"""Recompute inventories from retained host bytes, no native operations."""
import hashlib,json,sys,tarfile,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parents[2]))
from runtime.integration_checks.workload import summarize

def require(ok,message):
 if not ok:raise ValueError(message)
def main():
 cases=[('post-dispatch-inspection-01','calc','post-dispatch-inspection-primary-01'),
        ('post-dispatch-inspection-01','child-target','post-inspection-failure-primary-02'),
        ('post-dispatch-inspection-01','managed-target','post-inspection-failure-primary-03'),
        ('managed-target-ancestry-01','primary','managed-target-primary-01')]
 for bundle,prefix,report_name in cases:
  base=ROOT.parent/bundle;manifest=json.loads((base/'manifest.json').read_text())
  with tempfile.TemporaryDirectory() as td,tarfile.open(base/'raw.tar.gz') as archive:
   for member in archive.getmembers():
    parts=Path(member.name).parts
    if not member.isfile() or parts[:2]!=(prefix,'host'):continue
    require(len(parts)==3 and parts[2] not in ('.','..'),'flat host member')
    data=archive.extractfile(member).read();identity=manifest[member.name]
    require(len(data)==identity['bytes'] and hashlib.sha256(data).hexdigest()==identity['sha256'],'source hash')
    Path(td,parts[2]).write_bytes(data)
   actual=summarize(td);expected=json.loads((ROOT/(report_name+'.json')).read_text())
   require(actual==expected,'inventory changed: '+report_name)
 print(json.dumps({'status':'PASS','inventories':len(cases),'scope':'historical receipt accounting, not matched task performance'}))
if __name__=='__main__':main()
