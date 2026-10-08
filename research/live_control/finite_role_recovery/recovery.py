"""One pre-input recovery; unknown actions and wrong targets propagate."""
from . import pipeline

def run_with_one_recovery(task,editor,subject,record,reuse_label=True):
    task=dict(task) # Own the original string-valued request before callbacks.
    validated_label=None
    def infer(t,document):
        nonlocal validated_label
        output=subject(dict(t),document) # A callback cannot rewrite validation input.
        checked=pipeline.contract.validate_subject(document,t,output)
        if checked['outcome']=='READY':validated_label=output['changed_role']
        return output
    try:
        return pipeline.run_task(task,'retained_semantic_label',None,editor,infer,record)
    except pipeline.StaleDocument:
        if editor.replacements or editor.saves or validated_label is None:
            raise RuntimeError('STOP: recovery not authorized after input or without validated label')
        record('one_recovery_admitted',{'task_id':task['id']})
        current=editor.read_current() # Fresh selected-document/full-body observation.
        refreshed={**task,'document':current}
        # Original pipeline reobserves twice, computes against the current full body,
        # and invalidates a missing role before any input. A second stale body escapes.
        return pipeline.run_task(refreshed,'retained_semantic_label',validated_label if reuse_label else None,editor,infer,record)
