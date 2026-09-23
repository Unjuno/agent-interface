"""Read-only evidence of a saved value effect after zero completed steps."""
import hashlib,json,zipfile
from pathlib import Path
from openpyxl import load_workbook
H=Path(__file__).resolve().parent;R=H/'results/sampled-effect-calc-02'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
snapshots=read(R/'workbook-snapshots.json');turns=read(R/'turns.json')
def snapshot(label):
 s=next(x for x in snapshots if x['label']==label)
 assert s['read_status']=='bytes_copied_for_postrun_audit'
 assert sha(R/s['file'])==s['sha256']
 wb=load_workbook(R/s['file'],data_only=True)
 cells=[wb.active['A1'].value,wb.active['A2'].value];wb.close()
 return dict(s,cells=cells)
before=snapshot('after-sampling-1');after=snapshot('after-phase-2');pre_resave=snapshot('after-sampling-2')
t=turns[1]['phases']['result']['state']['last_resolution']['terminal']
assert t['status']=='needs_decision' and t['steps_completed']==0 and t['release']['verified']
assert before['cells']==[None,None] and after['cells']==pre_resave['cells']==[480,192]
assert pre_resave['finished_ns']<turns[2]['model_begin_ns']
assert any(s=={'op':'chord','modifier':'Control_L','key':'s'} for s in turns[2]['proposal']['steps'])
for row in turns:
 if row['feedback'] is not None:
  assert set(row['feedback'])=={'proposal','phase_status','reason','target_check','resolution','decision_samples'}
  prompt=(R/f"prompt-{row['turn']}.txt").read_text(encoding='utf-8')
  assert json.loads(prompt.split('Evidence: ')[1])==row['feedback']
with zipfile.ZipFile(R/after['file']) as a,zipfile.ZipFile(R/'runtime/sheet.xlsx') as b:
 names=sorted(set(a.namelist())|set(b.namelist()))
 changed=[n for n in names if n not in a.namelist() or n not in b.namelist() or a.read(n)!=b.read(n)]
result={'scope':'independent postrun parsing; declared cell values only, not arbitrary workbook equivalence or general GUI effects',
 'sources':{p.name:sha(p) for p in [Path(__file__),R/'workbook-snapshots.json',R/'turns.json']},
 'before':{'label':before['label'],'cells':before['cells']},
 'after':{'label':after['label'],'file':after['file'],'sha256':after['sha256'],'cells':after['cells']},
 'terminal':t,'already_persisted_before_next_model':True,'later_model_action':turns[2]['proposal'],
 'changed_zip_members_after_later_save':changed,'model_received_saved_snapshots':False,'authority':'none'}
(R/'persisted-effect-evidence.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'saved_cells_before_resave':after['cells'],'terminal_status':t['status'],'steps_completed':t['steps_completed'],'changed_zip_members_after_resave':changed}))
