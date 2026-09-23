import copy,json,subprocess,sys,tempfile
from pathlib import Path
import audit

def base_rows():
 rows=[]
 for rep in range(3):
  for s in ('stable','focus_transferred','observer_unavailable'):
   for p in ('naive_command','observed_guard'):
    r={'case_id':f'{s}-{p}-r{rep}','scenario':s,'policy':p,'status':'ok','held_observed':True,'release_observed':True,'neutral_final':True,'task_input_dispatched':False,'decision':'','app_effect':{'string':''},'helper_effect':''}
    if s=='stable':r['decision']='ACT';r['task_input_dispatched']=True;r['app_effect']['string']='7'
    elif s=='focus_transferred' and p=='naive_command':r['decision']='ACT';r['task_input_dispatched']=True;r['helper_effect']='7'
    elif s=='focus_transferred':r['decision']='REFUSE_MISMATCH'
    elif p=='naive_command':r['decision']='ACT';r['task_input_dispatched']=True;r['app_effect']['string']='7'
    else:r['decision']='REFUSE_UNKNOWN'
    rows.append(r)
 return rows

def main():
 rows=base_rows(); assert not audit.evaluate(rows)['errors']
 muts=[]
 def chk(name,fn):
  x=copy.deepcopy(rows);fn(x);muts.append((name,bool(audit.evaluate(x)['errors'])))
 chk('drop',lambda x:x.pop());chk('dup',lambda x:x.append(copy.deepcopy(x[0])));chk('hold',lambda x:x[0].__setitem__('held_observed',False));chk('release',lambda x:x[0].__setitem__('neutral_final',False));chk('stable',lambda x:x[0]['app_effect'].__setitem__('string',''));chk('wrong',lambda x:x[2].__setitem__('helper_effect',''));chk('guard_dispatch',lambda x:x[3].__setitem__('task_input_dispatched',True));chk('guard_wrong',lambda x:x[3].__setitem__('helper_effect','7'));chk('unknown',lambda x:x[5].__setitem__('decision','ACT'));chk('id',lambda x:x[1].__setitem__('case_id',x[0]['case_id']))
 assert all(v for _,v in muts),muts; print(json.dumps(muts));return 0
if __name__=='__main__':raise SystemExit(main())
