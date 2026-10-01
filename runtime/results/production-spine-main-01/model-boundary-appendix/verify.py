"""Post-hoc requested-configuration audit; never provider resolution or input."""
import importlib.util,json,re,sys,tarfile
from pathlib import Path
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent))
spec=importlib.util.spec_from_file_location('original_spine_verify',here.parent/'verify.py')
original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
def require(value,message):
 if not value:raise ValueError(message)
def read(name):return json.loads((here/name).read_text())
def verify():
 base=original.verify()
 projection=read('primary-model-call-projection.json');mapping=read('primary-model-input-map.json')
 calls=projection['calls'];require(len(calls)==46,'all selected calls')
 require(all(c['type']=='custom_tool_call' and c['name']=='exec' for c in calls),'actual outer tool calls')
 require(all(re.fullmatch(r'[0-9a-f]{64}',c['source_record_sha256']) for c in calls),'source record hashes')
 require([c['timestamp'] for c in calls]==sorted(c['timestamp'] for c in calls),'call ordering')
 require(all(c['context']['timestamp']<=c['timestamp'] for c in calls),'preceding configuration context')
 require({(c['context']['model'],c['context']['reasoning_effort']) for c in calls}=={('gpt-6.1-sol','medium')},'same requested configuration')
 for route,pattern in [('guarded',r"\bp2\.input\s*\(\s*'([^']+)'"),('direct',r"\bpd2\.direct\s*\(\s*'([^']+)'")]:
  key='alias' if route=='guarded' else 'phase'
  derived=[{key:m[1],'timestamp':c['timestamp'],'context':c['context'],'call_id':c['call_id']} for c in calls for m in re.finditer(pattern,c['input'])]
  require(derived==mapping[route],'input map derived from original call projection')
 require(len(mapping['guarded'])==25 and len(mapping['direct'])==12,'all input choices including expiry')
 with tarfile.open(here.parent/'raw.tar.gz','r:gz') as archive:
  def raw(name):return json.loads(archive.extractfile('production-spine-02/'+name).read())
  ordinary=[]
  for i in range(1,78):
   q=raw('guarded-local/host/request-'+str(i)+'.json');r=raw('guarded-local/host/reply-'+str(i)+'.json')
   if q['tool']=='interface_guarded_input' and not r['result']['isError']:ordinary.append(q['arguments']['alias'])
  # Choice14 samples an expired alias and dispatches no input. Its explicit fresh
  # successor is retained separately; never classify the clock-only choice as input.
  declared=[c['alias'] for c in mapping['guarded']]
  require(declared[14]=='save_off_b' and declared[:14]+declared[15:]==ordinary,'match every admitted guarded choice')
  phases=[c['phase'] for c in mapping['direct']]
  require(phases==[v for i in range(1,7) for v in ['nav'+str(i),'save'+str(i)]],'same direct task schedule')
  for phase,i in zip(phases,range(6,29,2)):
   q=raw('direct-post/host/request-'+str(i)+'.json')
   require(q['tool']=='interface_dispatch' and q['arguments']['program']['program_id'].startswith('production-spine02-'+phase+'-'),'match every direct program')
 return {'schema':'production-spine-posthoc-config-audit-v1','assessment':'PASS_INTEGRATION_SPINE_SCOPED','requested_model':'gpt-6.1-sol','requested_reasoning_effort':'medium','selected_outer_calls':46,'guarded_input_choices':25,'guarded_executed_programs':24,'direct_input_choices':12,'original_assessment_preserved':base['adoption'],'raw_archive_sha256':base['archive_sha256'],'scope':'Same Codex requested model/settings for all primary input choices, plus original scoped correctness audit. Selected turn context fields and tool records are projections. No provider-internal revision, model ingestion latency, isolated reasoning time, causal speedup, billing, human tempo or general product acceptance.'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
