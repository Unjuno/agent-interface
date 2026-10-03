"""Public observation/input gates; no native backend loaded here."""
from . import contract

class StaleDocument(RuntimeError):
    pass

def run_task(task,arm,retained_label,editor,subject,record):
    if arm not in ('plain_batched_ephemeral','retained_semantic_label'):
        raise ValueError('unknown arm')
    original=editor.read_current()
    record('observed_original',{'matches_public_input':original==task['document']})
    if original!=task['document']:raise RuntimeError('STOP: public original mismatch before model or input')
    change=None;label=retained_label
    if arm=='retained_semantic_label' and label is not None:
        change=contract.adapter.apply_role(original,label,task['old_person'],task['new_person'])
        record('reuse_contract',{'outcome':change['outcome'],'role':label})
        if change['outcome']=='INVALIDATED':
            record('invalidated_before_input',{'role':label})
            change=None
        elif change['outcome']!='READY':raise RuntimeError('STOP: retained contract refusal')
    if change is None:
        record('subject_attempt_before_send',{'task_id':task['id']})
        output=subject(task,original)
        if type(output) is dict:output=dict(output) # Own response fields before journaling.
        change=contract.validate_subject(original,task,output)
        record('subject_contract',{'outcome':change['outcome']})
        if change['outcome']!='READY':raise RuntimeError('STOP: subject contract refusal')
        label=output['changed_role']
    # Fresh observation after inference; no stale reference can authorize replacement.
    fresh=editor.read_current()
    record('revalidated_original',{'matches_previous':fresh==original})
    if fresh!=original:raise StaleDocument('STOP: document changed while planning')
    record('replacement_intent',{'task_id':task['id']})
    editor.replace_once(change['updated_text'])
    visible=editor.read_current()
    record('observed_replacement',{'matches_program':visible==change['updated_text']})
    if visible!=change['updated_text']:raise RuntimeError('STOP: replacement observation mismatch; no save')
    record('save_intent',{'task_id':task['id']})
    editor.save_once()
    record('save_returned',{'task_id':task['id']})
    return label if arm=='retained_semantic_label' else None
