from validator import surface_bound, RecoveryRejected
cur={'app':'INKSCAPE','client_id':22,'transient_for':11}
base={'app':'INKSCAPE','client_id':22,'transient_for':11,'authority':'none','task_input_granted':False,'action_admission_eligible':False}
assert surface_bound(dict(base),cur)['accepted']
controls=[]
for name,patch in [
 ('missing_surface',{'client_id':None}),
 ('forged_surface',{'client_id':23}),
 ('wrong_transient',{'transient_for':999}),
 ('authority',{'authority':'task'}),
 ('task_input',{'task_input_granted':True}),
 ('admission',{'action_admission_eligible':True}),
]:
    x=dict(base);x.update(patch)
    try:surface_bound(x,cur)
    except RecoveryRejected:controls.append(name)
    else:raise AssertionError(name)
print('controls PASS',len(controls))
