import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
EXPECTED_SHA256={'input_owner_v12.py':'b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508','adapter_contract.py':'ed7e4f00675e79a9ef86984c7c129bb6c3eda64855c6c71821c313c9feb9badf'}
EXPECTED_BLOBS={
 'research/doom/session_map01_v13.py':'51c644ce424e41bb2cd3d401a52b6c9820f70135',
 'research/doom/doom_retained_input_backend_v3.py':'65d3f1a7b21af09ab8fe10ef883e3e17a9f6cb27',
 'research/live_control/input_transition_owner_v3.py':'0ea631abcf6272f0538a9ef9198ad8069b47b464',
 'research/doom/fixtures/map01-threat-contact-v2/fixture.json':'2b898a68d38e14ac1981985dc58f295f18a06eaa',
}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def blob(p):
 b=Path(p).read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def static_compat(source,v12):
 sys.path[:0]=[str(source/'research/live_control'),str(v12),str(Path(__file__).parent)]
 from map01_v12_transition_owner import InputOwner
 class Cancel:
  def is_set(self):return False
 class Lease:pass
 lease=Lease();lease.intent_token='intent-1';lease.focus_invalid=False;lease.cancel=Cancel();lease.deadline=time.perf_counter_ns()+10_000_000_000
 class Fake:
  def __init__(self,_):self.owner_id='owner-1';self.records=[]
  def close(self):pass
  def call(self,op,lease=None,key=None):
   if op=='down':return {'event':'input_admission','key':key,'physical_key_measurement':{'adapter_edge':{'edge':'down','status':'CONFIRMED_PHYSICAL_DOWN','actuation_id':'act-1','owner_id':self.owner_id,'intent_token':lease.intent_token,'key':key,'interval':[10,20]}}}
   if op=='up':return {'event':'input_release_measurement','key':key,'grants_input_authority':False,'physical_key_measurement':{'adapter_edge':{'edge':'up','status':'CONFIRMED_PHYSICAL_UP','actuation_id':'act-1','owner_id':self.owner_id,'intent_token':lease.intent_token,'key':key,'interval':[30,40]},'sentinel':17}}
   if op=='input_state':return {'owner_id':self.owner_id,'owned_keycodes':[],'sample_started_ns':50,'sample_finished_ns':51}
   if op=='button_up':return None
   return None
 x=InputOwner(':fake',_owner_cls=Fake);d=x.call('down',lease,'a');u=x.call('up',lease,'a');b=x.call('button_up',lease,1);st=x.call('input_state')
 return d.get('intent_token')=='intent-1' and u.get('transition_schema')=='input-release-transition-v3' and u.get('physical_key_measurement',{}).get('sentinel')==17 and u['physical_key_measurement']['adapter_edge']['interval']==[30,40] and u.get('grants_input_authority') is False and u.get('ordinary_release_candidate') is True and b.get('operation')=='button_up' and 'physical_key_measurement' not in b and st.get('owned_keycodes')==[]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--v12',type=Path,required=True);a=ap.parse_args();a.source=a.source.resolve();a.v12=a.v12.resolve();err=[]
 got_sha={n:sha(a.v12/n) for n in EXPECTED_SHA256};got_blob={n:blob(a.source/n) for n in EXPECTED_BLOBS}
 err += [f'hash:{n}' for n,h in EXPECTED_SHA256.items() if got_sha.get(n)!=h]
 err += [f'blob:{n}' for n,h in EXPECTED_BLOBS.items() if got_blob.get(n)!=h]
 cp=subprocess.run([sys.executable,'-m','py_compile',*[str(x) for x in Path(__file__).parent.glob('*.py')]],capture_output=True,text=True)
 if cp.returncode:err.append('compile:'+cp.stderr)
 try:
  if not static_compat(a.source,a.v12):err.append('static_compat')
 except Exception as exc:err.append('static_compat_exc:'+repr(exc))
 out={'passed':not err,'errors':err,'v12_sha256':got_sha,'source_git_blobs':got_blob,'static_compat_passed':'static_compat' not in err and not any(x.startswith('static_compat_exc') for x in err)}
 print(json.dumps(out,sort_keys=True));raise SystemExit(0 if not err else 1)
if __name__=='__main__':main()
