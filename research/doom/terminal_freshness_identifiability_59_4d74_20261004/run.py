import hashlib, importlib.util, json, pathlib, sys
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
SOURCE=HERE/'source/independent_progress_clock_v2.py'
SOURCE_SHA='3d906a7043f0d674bac3bd137952adeac11c77c9339bc38ef6ca37b05e0d1613'
PLAN_SHA='fd880f066d5762f24ae65899a0122f062ccb871997c03d54e9c1074929f2b730'
def need(value,message):
 if not value: raise SystemExit(message)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
need(sha(SOURCE)==SOURCE_SHA,'frozen source hash mismatch')
need(sha(HERE/'PLAN.md')==PLAN_SHA,'frozen plan hash mismatch')
spec=importlib.util.spec_from_file_location('clock_v2_frozen',SOURCE)
clock=importlib.util.module_from_spec(spec); sys.modules[spec.name]=clock; spec.loader.exec_module(clock)
def run_samples(seq):
 c=clock.ProgressClock(); events=[]
 for row in seq: events.extend(c.ingest(clock.ProgressSample(**row)))
 return events
BASE={'sample_ns':1_000_000_000,'kill_count':0,'death_count':0,'episode_finished':False,'player_dead':False,'map_exit':False}
traces=[]
for case,end in [
 ('positive_kill',{'sample_ns':2_000_000_000,'kill_count':1,'death_count':0,'episode_finished':False,'player_dead':False,'map_exit':False}),
 ('terminal_no_exit',{'sample_ns':2_000_000_000,'kill_count':0,'death_count':0,'episode_finished':True,'player_dead':False,'map_exit':False})]:
 samples=[BASE,end]
 fresh={'producer_epoch':'current-episode-42','update_epoch':74,'samples':samples}
 stale={'producer_epoch':'previous-episode-41','update_epoch':74,'samples':samples}
 traces.append({'case':case,'fresh':{'provenance':{k:fresh[k] for k in ('producer_epoch','update_epoch')},'events':run_samples(fresh['samples'])},'stale':{'provenance':{k:stale[k] for k in ('producer_epoch','update_epoch')},'events':run_samples(stale['samples'])}})
field_names=[x.name for x in clock.dataclasses.fields(clock.ProgressSample)] if hasattr(clock,'dataclasses') else [x.name for x in __import__('dataclasses').fields(clock.ProgressSample)]
raw={'status':'captured','source_commit':'5489741c1efa2d25bedf5aa64e60a68fb2f74e3c','source_sha256':sha(SOURCE),'plan_sha256':sha(HERE/'PLAN.md'),'api_fields':field_names,'serialized_sample_fields':sorted(clock.ProgressSample(**BASE).as_dict()),'traces':traces,'external_engine_or_input':False}
(HERE/'RAW.json').write_text(json.dumps(raw,indent=2,sort_keys=True)+'\n')
print(json.dumps(raw,indent=2,sort_keys=True))
