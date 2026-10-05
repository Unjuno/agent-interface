import ast, hashlib, json, sys, time
from pathlib import Path

src = Path(__file__).with_name('controller_source.py')
tree = ast.parse(src.read_text(encoding='utf-8'))
wanted = {'_typed_json_equal','_signal_pair_matches','_signal_pair_content_matches','DoomCoverSignalPairMonitor'}
nodes = [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in wanted]
assert {n.name for n in nodes} == wanted
subset = ast.Module(body=nodes, type_ignores=[])
ns={'time':time}
exec(compile(subset,str(src),'exec'),ns)
class Guard:
    def __init__(self,name,floor):
        self.spec={'source_value':80 if name=='health' else 10,'source_sequence':1}
        self.source_capture_ns=100
        self.name=name; self.floor=floor
    def evaluate(self,s):
        v=s['value']
        if v < self.floor:
            return {'status':'HARD_INVALIDATED','reason':'below_floor','requires_new_decision':True,'hard_minimum':self.floor,'current_value':v,'task_success_verified':False}
        return {'status':'SOFT_CHANGED','reason':'changed','requires_new_decision':False,'hard_minimum':self.floor,'current_value':v,'task_success_verified':False}
class Reader:
    def __init__(self,name): self.name=name
    def read(self,o): return o['signals'][self.name]
def sig(name,value,seq=2,cap=200,binding=None):
    return {'status':'observed','signal_id':name,'value':value,'sequence':seq,'capture_ns':cap,'binding':binding if binding is not None else {'window':7}}
def obs(event='typed_observation',h=75,a=9,seq=2,cap=200,binding=None,frame='f'*64,hs=None,am=None):
    b=binding if binding is not None else {'window':7}
    return {'event':event,'sequence':seq,'capture_ns':cap,'pointer_binding':b,'frame_rgb_sha256':frame,
      'signals':{'health':hs if hs is not None else sig('health',h,seq,cap,b),'ammo':am if am is not None else sig('ammo',a,seq,cap,b)}}
def monitor():
    return ns['DoomCoverSignalPairMonitor']({'health':Guard('health',51),'ammo':Guard('ammo',1)},Reader('health'),Reader('ammo'))
cases=[]
def reason(result): return result.get('reason') if isinstance(result,dict) else result
def record(name,got,expected): cases.append({'case':name,'observed':got,'expected':expected,'pass':got==expected})
record('valid_pair_preserves_cover',monitor().observe(obs()),None)
record('health_ammo_sequence_mismatch',reason(monitor().observe(obs(am=sig('ammo',9,1,200)))), 'signal_pair_epoch_mismatch')
record('health_ammo_capture_mismatch',reason(monitor().observe(obs(am=sig('ammo',9,2,199)))), 'signal_pair_epoch_mismatch')
record('health_ammo_binding_mismatch',reason(monitor().observe(obs(am=sig('ammo',9,2,200,{'window':8})))), 'signal_pair_epoch_mismatch')
record('health_below_floor', (monitor().observe(obs(h=50)) or {}).get('reason'), 'health:below_floor')
record('ammo_below_floor', (monitor().observe(obs(a=0)) or {}).get('reason'), 'ammo:below_floor')
m=monitor(); first=m.observe(obs()); second=m.observe(obs(event='observation')); record('duplicate_epoch_same_projection',second,None)
m=monitor(); m.observe(obs()); second=m.observe(obs(event='observation',frame='e'*64)); record('duplicate_epoch_frame_disagreement',second.get('reason') if second else None,'signal_pair_duplicate_epoch_mismatch')
bad=obs(); bad['signals'].pop('ammo'); record('missing_typed_signal',monitor().observe(bad).get('reason'),'signal_pair_epoch_mismatch')
raw={'source_file':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'extract':'AST-selected exact helper/class definitions; dependencies stubbed only at ObservableSignalGuard/reader interfaces','cases':cases,'pass_count':sum(x['pass'] for x in cases),'case_count':len(cases),'real_input_used':False,'live_game_used':False,'planner_used':False}
Path(sys.argv[1]).write_text(json.dumps(raw,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pass_count':raw['pass_count'],'case_count':raw['case_count'],'source_sha256':raw['source_sha256']}))



