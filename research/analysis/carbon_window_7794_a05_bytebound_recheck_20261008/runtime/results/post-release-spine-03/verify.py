import hashlib,importlib.util,json,pathlib,tarfile,tempfile,sys
def require(ok,why):
 if not ok:raise ValueError(why)
def verify(folder):
 folder=pathlib.Path(folder);manifest=json.loads((folder/'manifest.json').read_text());archive=folder/'raw.tar.gz'
 require(hashlib.sha256(archive.read_bytes()).hexdigest()==manifest['archive_sha256'],'archive hash')
 with tempfile.TemporaryDirectory() as d:
  dest=pathlib.Path(d)
  with tarfile.open(archive,'r:gz') as tf:
   members=tf.getmembers()
   require(all(m.isfile() and not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts for m in members),'unsafe member')
   require(len(members)==len(manifest['members']) and {m.name for m in members}==set(manifest['members']),'member inventory')
   for m in members:
    data=tf.extractfile(m).read();require(hashlib.sha256(data).hexdigest()==manifest['members'][m.name],'member hash '+m.name)
    path=dest/m.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    import os
    os.utime(path,(m.mtime,m.mtime))
  spec=importlib.util.spec_from_file_location('retained_analysis',dest/'analyze-v2.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  expected_guard=['interface_guarded_observe','interface_guarded_mint_many','interface_guarded_input','interface_guarded_mint_many']+['interface_guarded_input']*5+['interface_close']
  expected_direct=['interface_validate']*3+['interface_observe']+['interface_clock','interface_dispatch']*12+['interface_close']
  for route,expected in [('guarded-local',expected_guard),('direct-post',expected_direct)]:
   actual=[json.loads((dest/route/'host'/f'request-{a}.json').read_text())['tool'] for a in range(1,len(expected)+1)]
   require(actual==expected,'no extra/replayed request schedule')
  result=module.analyze(dest);require(json.loads(json.dumps(result))==json.loads((dest/'analysis-v2.json').read_text()),'recomputed analysis')
  usage=json.loads((dest/'model-usage-projection.json').read_text());require(len(usage['calls'])==29 and len({x['call_id'] for x in usage['calls']})==29,'usage call inventory')
  require(all(x['local_context']['model']=='gpt-6.1-sol' and x['local_context']['effort']=='medium' and x['usage_records_before_output'] for x in usage['calls']),'observed model usage')
  return {'status':result['status'],'members':len(members),'guarded_exact':result['routes']['guarded-local']['score']['record_count'],'direct_exact':result['routes']['direct-post']['score']['record_count'],'input_replay':0,'scope':'Retained failure/comparison verification; not product acceptance'}
if __name__=='__main__':print(json.dumps(verify(sys.argv[1] if len(sys.argv)>1 else pathlib.Path(__file__).parent),indent=2))
