import itertools,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def br(when,outcome,action=None,next_state=None,reason=None):return {'when':when,'outcome':outcome,'action':action,'next_state':next_state,'reason':reason}
def sym(deps):return {'dependencies':deps}
def chromium():
 return {'name':'chromium-v5','predicates':['field_pixels_changed','field_target_present','submit_target_present','submission_pixels_changed'],'symbols':{'value_field':sym(['field_target_present','field_pixels_changed']),'submit_control':sym(['submit_target_present','field_pixels_changed'])},'actions':{'enter_token':{'symbol':'value_field','expected':{'field_pixels_changed':True}},'submit_form':{'symbol':'submit_control','expected':{'submission_pixels_changed':True}}},'initial':'empty','states':{'empty':[br({'field_pixels_changed':False,'field_target_present':True},'action','enter_token','filled')],'filled':[br({'field_pixels_changed':True,'submit_target_present':True},'action','submit_form','submitted')],'submitted':[br({'submission_pixels_changed':True},'complete')]},'domains':{'field_pixels_changed':[False,True,'unknown'],'field_target_present':[False,True],'submit_target_present':[False,True],'submission_pixels_changed':[False,True,'unknown']}}
def xterm(name='xterm-live-v4'):
 return {'name':name,'predicates':['surface_present','stage'],'symbols':{'surface':sym(['surface_present'])},'actions':{'token':{'symbol':'surface','expected':{'surface_present':True,'stage':'BLUE'}},'confirm':{'symbol':'surface','expected':{'surface_present':True,'stage':'GREEN'}}},'initial':'token','states':{'token':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'stage':'RED'},'action','token','confirm')],'confirm':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'stage':'BLUE'},'action','confirm','done'),br({'surface_present':True,'stage':'YELLOW'},'yield',reason='association_changed')],'done':[br({'surface_present':True,'stage':'GREEN'},'complete'),br({'surface_present':False},'yield',reason='association_changed')]},'domains':{'surface_present':[False,True],'stage':['RED','BLUE','GREEN','YELLOW','UNKNOWN']}}
def map01():
 return {'name':'map01-composition','predicates':['surface_present','phase'],'symbols':{'surface':sym(['surface_present'])},'actions':{'retreat':{'symbol':'surface','expected':{'surface_present':True,'phase':'STRAFE'}},'strafe':{'symbol':'surface','expected':{'surface_present':True,'phase':'DONE'}}},'initial':'retreat_state','states':{'retreat_state':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'phase':'RETREAT'},'action','retreat','strafe_state')],'strafe_state':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'phase':'STRAFE'},'action','strafe','done')],'done':[br({'surface_present':True,'phase':'DONE'},'complete'),br({'surface_present':False},'yield',reason='association_changed')]},'domains':{'surface_present':[False,True],'phase':['RETREAT','STRAFE','DONE','OTHER']}}
def continuous():
 return {'name':'continuous-control','predicates':['surface_present','zone'],'symbols':{'surface':sym(['surface_present'])},'actions':{'move_left':{'symbol':'surface','expected':{'surface_present':True}},'move_right':{'symbol':'surface','expected':{'surface_present':True}}},'initial':'steer','states':{'steer':[br({'surface_present':False},'yield',reason='association_changed'),br({'surface_present':True,'zone':'RIGHT'},'action','move_left','steer'),br({'surface_present':True,'zone':'LEFT'},'action','move_right','steer'),br({'surface_present':True,'zone':'GOAL'},'complete')]},'domains':{'surface_present':[False,True],'zone':['RIGHT','LEFT','GOAL','OTHER']}}
def desktop():s=xterm('desktop-cross-domain');return s
def incoming_expected(spec,state):
 keys=set()
 for branches in spec['states'].values():
  for b in branches:
   if b['outcome']=='action' and b['next_state']==state:keys.update(spec['actions'][b['action']]['expected'])
 return keys
def required(spec,state):
 keys=set()
 for b in spec['states'][state]:
  keys.update(b['when'])
  if b['outcome']=='action':keys.update(spec['symbols'][spec['actions'][b['action']]['symbol']]['dependencies'])
 keys.update(incoming_expected(spec,state));return sorted(keys)
def classify(branches,obs):
 matches=[i for i,b in enumerate(branches) if all(obs.get(k)==v for k,v in b['when'].items())]
 return ('none',) if not matches else ('one',matches[0]) if len(matches)==1 else ('many',tuple(matches))
rows=[];failures=[]
for spec in [chromium(),xterm(),map01(),continuous(),desktop()]:
 total=0;reqmap={}
 for state in spec['states']:
  req=required(spec,state);reqmap[state]=req
  for vals in itertools.product(*[spec['domains'][n] for n in spec['predicates']]):
   full=dict(zip(spec['predicates'],vals));projected={k:full[k] for k in req};total+=1
   if classify(spec['states'][state],full)!=classify(spec['states'][state],projected):failures.append([spec['name'],state,full,req])
   for b in spec['states'][state]:
    if b['outcome']=='action' and not set(spec['symbols'][spec['actions'][b['action']]['symbol']]['dependencies'])<=set(req):failures.append(['symbol',spec['name'],state])
   if not incoming_expected(spec,state)<=set(req):failures.append(['effect',spec['name'],state])
 rows.append({'spec':spec['name'],'global_predicates':len(spec['predicates']),'states':{s:{'required':reqmap[s],'required_count':len(reqmap[s]),'reduction_fraction':1-len(reqmap[s])/len(spec['predicates'])} for s in spec['states']},'finite_state_cases':total})
assert not failures
result={'pass':True,'specs':rows,'failures':failures,'total_finite_state_cases':sum(x['finite_state_cases'] for x in rows)}
(OUT/'cross_domain_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
