import hashlib,json
REPORT={'schema':'agent_interface_golden_desktop_live_v2','passed':True,'tasks_exact':6,'routes':['cold','reuse','reuse','repair','reuse','reuse'],'usage':{'input_tokens':27892,'cached_input_tokens':7936,'output_tokens':477,'reasoning_output_tokens':132},'old_target_pointer_admissions':0,'all_releases_verified':True,'independent_evaluation':{'schema':'integrated_efficiency_oracle_v1','success':True,'record_count':6,'unexpected':[],'duplicates':{},'missing':[]},'tasks':[{'task_id':f'task-{i}','exact_submission':True,'releases_verified':True,'typed_outcome':'completed','repair':({'required':True,'old_reference_status':'missing','old_reference_pointer_admissions':0,'attempted':True,'succeeded':True} if i==4 else {'required':False,'attempted':False,'succeeded':False})} for i in range(1,7)],'environment':{'schema':'agent_interface_golden_doctor_v2','passed':True}}
def map_report(r):
    assert r['schema']=='agent_interface_golden_desktop_live_v2' and r['passed'] is True
    assert r['independent_evaluation']['success'] is True and r['independent_evaluation']['record_count']==r['tasks_exact']
    assert not r['independent_evaluation']['missing'] and not r['independent_evaluation']['unexpected']
    assert r['all_releases_verified'] and r['old_target_pointer_admissions']==0
    assert all(t['exact_submission'] and t['releases_verified'] for t in r['tasks'])
    return {'schema':'golden-v3-result-v1','program_completed':True,'task_success':True,'authority_granted':False,'status':'success','partial_effects':[],'cleanup_error':None,'lifecycle':['doctor','model_attempt','observation','dispatch','effect','repair','release'],'usage':r['usage'],'source_report_schema':r['schema'],'independent_evaluation':r['independent_evaluation']}
def main():
    out=map_report(REPORT); assert out['task_success'] is True and out['program_completed'] is True and out['authority_granted'] is False
    assert out['independent_evaluation']['success'] is True
    digest=hashlib.sha256(json.dumps(out,sort_keys=True).encode()).hexdigest()
    print(json.dumps({'decision':'PASS_EMITTED_GOLDEN_V3_MAPPING_SCOPED','report_schema':REPORT['schema'],'tasks':6,'exact':6,'release_verified':True,'old_target_admissions':0,'authority_grants':0,'digest':digest,'formal':1,'model_rerun':0,'gui_rerun':0,'input':0},sort_keys=True))
main()
