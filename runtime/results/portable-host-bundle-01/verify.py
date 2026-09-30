import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def require(ok,label):
 if not ok:raise ValueError(label)
def main():
 manifest=json.loads((ROOT/'manifest.json').read_bytes())
 with tarfile.open(ROOT/'raw.tar.gz') as t:files={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
 require(set(files)==set(manifest),'members')
 for name,data in files.items():require(len(data)==manifest[name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[name]['sha256'],name)
 def read(name):return json.loads(files[name])
 runtime=read('manifest.json');host=read('host/HOST_MANIFEST.json')
 require(runtime['source_revision']==host['source_revision'] and runtime['host_bundle']['manifest']==host,'same pinned revision')
 require(hashlib.sha256(files['runtime.pyz']).hexdigest()==runtime['sha256'],'archive hash')
 for line in files['host/SHA256SUMS'].decode().splitlines():
  digest,name=line.split('  ',1);require(hashlib.sha256(files['host/'+name]).hexdigest()==digest,'host checksum')
 require([read(f'transport/request-{i}.json')['tool'] for i in range(1,4)]==['list_tools','interface_validate','interface_close'],'calls')
 result=read('probe-result.json');require(result['status']=='PASS' and result['calls']==3,'probe')
 require(result['validation']['static_valid'] is False,'static invalid')
 require(result['close']['status']=='closed' and result['close']['connection_close_attempted'] is False,'no backend opened')
 require(read('transport/exit.json')['code']==0 and result['exit']['code']==0,'terminal')
 require(not any(n.startswith('native_') for n in result['tools']) and 'interface_dispatch' in result['tools'],'public discovery')
 print(json.dumps({'status':'PASS','files':len(files),'scope':'retained construction only; no GUI or performance claim'}))
if __name__=='__main__':main()
