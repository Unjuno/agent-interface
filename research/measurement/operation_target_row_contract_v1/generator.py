import random,copy
OPS=['CLICK','TYPE_TEXT','SCROLL']; NON=['WATCH','NO_LOCAL_ACTION','YIELD','DONE_CANDIDATE']
def base(i,rng):
    obs=f'o{i}'; epoch=i%7; ops=OPS[:]
    targets=[{'target_id':'t0','observation_ref':obs,'observation_epoch':epoch,'operations':['CLICK','TYPE_TEXT']},{'target_id':'t1','observation_ref':obs,'observation_epoch':epoch,'operations':['CLICK','SCROLL']}]
    mv={'intent_id':f'i{i%13}','observation_ref':obs,'observation_epoch':epoch,'allowed_operations':ops,'targets':targets,'payload_refs':['p0','p1'],'prior_receipt_refs':[] if i%2 else ['r0']}
    kind=rng.randrange(8)
    if kind==0: disp='ACTION_SET'; acts=[{'operation':'CLICK','target_id':'t0'}]; done=None
    elif kind==1: disp='ACTION_SET'; acts=[{'operation':'TYPE_TEXT','target_id':'t0','payload_ref':'p0'}]; done=None
    elif kind==2: disp='ACTION_SET'; acts=[{'operation':'SCROLL','target_id':'t1','delta':1 if i%2 else -2}]; done=None
    elif kind==3: disp='ACTION_SET'; acts=[{'operation':'CLICK','target_id':'t0'},{'operation':'CLICK','target_id':'t1'}]; done=None
    else:
        disp=NON[kind-4]; acts=[]; done=f'v{i}' if disp=='DONE_CANDIDATE' else None
    return {'row_id':f'row{i}','episode_id':f'ep{i//4}','split_group':f'g{i//8}','split':'train' if (i//8)%2==0 else 'eval','model_visible':mv,'oracle':{'disposition':disp,'acceptable_actions':acts,'oracle_source_ref':f'oracle{i}','independent':True,'postdecision_refs':[f'post{i}'],'done_verifier_ref':done},'grants_input_authority':False}

def mutate(r,kind):
    x=copy.deepcopy(r)
    if kind==0:x['model_visible']['future_effect']='bad'
    elif kind==1:x['model_visible']['targets'][0]['observation_epoch']+=1
    elif kind==2:x['model_visible']['allowed_operations'].append('SHELL')
    elif kind==3:
        x['oracle']['disposition']='ACTION_SET';x['oracle']['done_verifier_ref']=None;x['oracle']['acceptable_actions']=[{'operation':'TYPE_TEXT','target_id':'t0','text':'invented'}]
    elif kind==4:x['row_id']=' '
    elif kind==5:x['model_visible']['targets'].append(copy.deepcopy(x['model_visible']['targets'][0]))
    elif kind==6:
        x['oracle']['disposition']='ACTION_SET';x['oracle']['done_verifier_ref']=None;x['oracle']['acceptable_actions']=[{'operation':'SCROLL','target_id':'t0','delta':1}]
    elif kind==7:
        x['oracle']['disposition']='DONE_CANDIDATE';x['oracle']['acceptable_actions']=[];x['oracle']['done_verifier_ref']=None
    elif kind==8:x['grants_input_authority']=True
    elif kind==9:x['oracle']['independent']=False
    return x
