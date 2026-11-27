"""Syntactic collateral-preservation contract, not a semantic oracle."""
from . import role_method as adapter

def validate_subject(document,task,output):
    keys={'updated_text','changed_role','previous_person','new_person','untouched_title'}
    if type(output) is not dict or set(output)!=keys or any(type(v) is not str for v in output.values()):
        return {'outcome':'REFUSE','reason':'invalid_subject_schema'}
    if output['previous_person']!=task['old_person'] or output['new_person']!=task['new_person'] or output['untouched_title']!='sibling.txt':
        return {'outcome':'REFUSE','reason':'request_parameter_mismatch'}
    change=adapter.apply_role(document,output['changed_role'],task['old_person'],task['new_person'])
    if change['outcome']!='READY':return change
    if output['updated_text']!=change['updated_text']:
        return {'outcome':'REFUSE','reason':'changed_other_content'}
    return change
