import hashlib,json,tarfile
from pathlib import Path
def require(value,message):
    if not value:raise ValueError(message)
root=Path(__file__).resolve().parent;manifest=json.loads((root/'manifest.json').read_text())['files'];raw={}
with tarfile.open(root/'raw.tar.gz') as archive:
    members=archive.getmembers();require(len(members)==len(manifest) and {m.name for m in members}==set(manifest),'members')
    for member in members:
        require(member.isfile(),'regular file');data=archive.extractfile(member).read();raw[member.name]=data
        require(len(data)==manifest[member.name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[member.name]['sha256'],'bytes')
p='results-local/public-title-calc-02/'
comparison=json.loads(raw[p+'comparison.json']);before=comparison['before'];after=comparison['after']
require(before['title']=='' and after['title']=='sheet.xlsx — LibreOffice Calc','title recovery')
require({k:v for k,v in before.items() if k!='title'}=={k:v for k,v in after.items() if k!='title'},'unchanged target evidence')
require(comparison['backend_emissions']==0,'no task input')
require('_NET_WM_NAME(UTF8_STRING) = "sheet.xlsx — LibreOffice Calc"' in raw[p+'xprop.stdout'].decode(),'independent property read')
require(json.loads(raw[p+'xprop-exit.json'])['returncode']==0,'xprop exit')
for run in ('public-title-calc-01','public-title-calc-02'):
    require(all(row['returncode'] is not None for row in json.loads(raw['results-local/'+run+'/cleanup.json'])),'process cleanup')
require('TypeError' in json.loads(raw['results-local/public-title-calc-01/setup-failure.json'])['error'],'preserved setup failure')
for kind,count in (('protocol',272),('harness',125)):
    log=raw[f'results-local/public-title-native-01/{kind}.stderr.log']
    require(f'Ran {count} tests'.encode() in log and b'\nOK\n' in log,'local checks')
print(f'PASS: {len(raw)} retained files; real Calc title recovered without task input')
