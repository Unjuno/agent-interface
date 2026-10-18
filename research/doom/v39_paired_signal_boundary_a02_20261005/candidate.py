import ast, copy, hashlib, json, sys, time
from pathlib import Path
src=Path(__file__).with_name('controller_source.py')
tree=ast.parse(src.read_text(encoding='utf-8'))
wanted={'_typed_json_equal','_signal_pair_matches','_signal_pair_content_matches','DoomCoverSignalPairMonitor'}
nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in wanted]
assert {n.name for n in nodes}==wanted
ns={'time':time}; exec(compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec'),ns)
class Guard:
 def __init__(self,name,floor): self.spec={'source_value':80 if name=='health' else 10,'source_sequence':1}; self.source_capture_ns=100; self.name=name; self.floor=floor
 def evaluate(self,s):
  v=s['value']; hard=v<self.floor
  return {'status':'HARD_INVALIDATED' if hard else 'SOFT_CHANGED','reason':'below_floor' if hard else 'changed','requires_new_decision':hard,'grants_input_authority':False,'may_only_preserve_or_reduce_existing_authority':True,'hard_minimum':self.floor,'current_value':v,'task_success_verified':False}
class Reader:
 def __init__(self,name): self.name=name
 def read(self,o): return o['signals'][self.name]
def sig(name,value,seq=2,cap=200,binding=None): return {'status':'observed','signal_id':name,'value':value,'sequence':seq,'capture_ns':cap,'binding':binding if binding is not None else {'window':7}}
def obs(event='typed_observation',h=75,a=9,seq=2,cap=200,binding=None,frame='f'*64,hs=None,am=None):
 b=binding if binding is not None else {'window':7}
 return {'event':event,'sequence':seq,'capture_ns':cap,'pointer_binding':b,'frame_rgb_sha256':frame,'signals':{'health':hs if hs is not None else sig('health',h,seq,cap,b),'ammo':am if am is not None else sig('ammo',a,seq,cap,b)}}
def monitor(): return ns['DoomCoverSignalPairMonitor']({'health':Guard('health',51),'ammo':Guard('ammo',1)},Reader('health'),Reader('ammo'))
def receipt(result):
 if result is None: return None
 return {k:copy.deepcopy(result.get(k)) for k in ('event','reason','outcome','outcomes','requires_new_decision','grants_input_authority')}
expect={'valid_pair_preserves_cover':(None,None),'health_ammo_sequence_mismatch':('signal_pair_epoch_mismatch','UNKNOWN'),'health_ammo_capture_mismatch':('signal_pair_epoch_mismatch','UNKNOWN'),'health_ammo_binding_mismatch':('signal_pair_epoch_mismatch','UNKNOWN'),'health_below_floor':('health:below_floor','HARD_INVALIDATED'),'ammo_below_floor':('ammo:below_floor','HARD_INVALIDATED'),'duplicate_epoch_same_projection':(None,None),'duplicate_epoch_frame_disagreement':('signal_pair_duplicate_epoch_mismatch','UNKNOWN'),'missing_typed_signal':('signal_pair_epoch_mismatch','UNKNOWN')}
rows=[]
def add(name,result):
 r=receipt(result); er,es=expect[name]
 passed=(r is None) if er is None else bool(r and r['event']=='paired_signal_invalidation' and r['reason']==er and r['requires_new_decision'] is True and r['grants_input_authority'] is False and r['outcome']['status']==es and r['outcome']['requires_new_decision'] is True and r['outcome']['grants_input_authority'] is False and r['outcome']['task_success_verified'] is False and r['outcome']['may_only_preserve_or_reduce_existing_authority'] is True)
 rows.append({'case':name,'observed':r,'expected':{'reason':er,'outcome_status':es},'pass':passed})
add('valid_pair_preserves_cover',monitor().observe(obs()))
add('health_ammo_sequence_mismatch',monitor().observe(obs(am=sig('ammo',9,1,200))))
add('health_ammo_capture_mismatch',monitor().observe(obs(am=sig('ammo',9,2,199))))
add('health_ammo_binding_mismatch',monitor().observe(obs(am=sig('ammo',9,2,200,{'window':8}))))
add('health_below_floor',monitor().observe(obs(h=50)))
add('ammo_below_floor',monitor().observe(obs(a=0)))
m=monitor(); m.observe(obs()); add('duplicate_epoch_same_projection',m.observe(obs(event='observation')))
m=monitor(); m.observe(obs()); add('duplicate_epoch_frame_disagreement',m.observe(obs(event='observation',frame='e'*64)))
bad=obs(); bad['signals'].pop('ammo'); add('missing_typed_signal',monitor().observe(bad))
raw={'schema':'v39-paired-signal-outcome-a02','source_path':'research/doom/map01_overlap_controller_v39.py','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'cases':rows,'pass_count':sum(x['pass'] for x in rows),'case_count':len(rows),'real_input_used':False,'live_game_used':False,'planner_used':False}
Path(sys.argv[1]).write_text(json.dumps(raw,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pass_count':raw['pass_count'],'case_count':len(rows),'source_sha256':raw['source_sha256']}))
if raw['pass_count']!=9: raise SystemExit(1)
