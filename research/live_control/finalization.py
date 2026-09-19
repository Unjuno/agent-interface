"""Post-controller finalization stages; publication is not model acknowledgement."""
import copy
import time


def finalize(program_id, close_admission, evaluate, publish):
    result = dict(final_program=program_id, started_ns=time.perf_counter_ns(),
                  admission_closed=False, evaluation=None, output_flushed=False)
    stage = 'close_admission'
    try:
        close_admission()
        result['admission_closed'] = True
        stage = 'evaluate'
        evaluation = evaluate()
        if not isinstance(evaluation, dict) or type(evaluation.get('success')) is not bool:
            raise ValueError('evaluation must contain boolean success')
        result['evaluation'] = copy.deepcopy(evaluation)
        stage = 'publish'
        if publish(dict(event='independent_evaluation', final_program=program_id, **evaluation)) is not True:
            raise OSError('evaluation output not confirmed flushed')
        result['output_flushed'] = True
        result['status'] = 'finished'
    except Exception as exc:
        result.update(status='finalization_error', failure_stage=stage,
                      error=dict(type=type(exc).__name__, message=str(exc)))
    result['finished_ns'] = time.perf_counter_ns()
    return result
