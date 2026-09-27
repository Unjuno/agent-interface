from classify import classify
base={'clock_provenance':{'clock_domain_retained':True,'clock_epoch_retained':True},'endpoints':{k:{'status':'RECORDED'} for k in ['planner_request','planner_response','action_accept','input_ack','first_useful_effect','observation_ready','terminal_verified']}}
assert classify(base)['reportable_count']==6
base['endpoints']['first_useful_effect']={'status':'NOT_RECORDED'}
assert classify(base)['reportable_count']==3
base['clock_provenance']['clock_epoch_retained']=False
assert classify(base)['reportable_count']==0
print('construction PASS 3/3')
