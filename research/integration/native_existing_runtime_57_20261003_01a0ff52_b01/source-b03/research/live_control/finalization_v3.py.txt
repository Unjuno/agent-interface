"""Post-controller finalization stages; publication is not model acknowledgement."""
import copy
import time


def finalize(program_id, close_admission, evaluate, publish, observe_effect=None):
    result = dict(final_program=program_id, started_ns=time.perf_counter_ns(),
                  admission_closed=False, evaluation=None, output_flushed=False)
    stage = 'close_admission'
    try:
        close_admission()
        result['admission_closed'] = True
        if observe_effect is not None:
            stage = 'observe_effect'
            result['effect'] = copy.deepcopy(observe_effect())
            if not isinstance(result['effect'],dict) or result['effect'].get('status') not in ('VERIFIED','CONTRADICTED','UNKNOWN'):
                raise ValueError('invalid effect evidence')
        if observe_effect is not None:
            result['effect_output_flushed']=False
            result['effect_publish_started_ns']=time.perf_counter_ns()
            try:
                if publish(dict(event='effect_evidence',final_program=program_id,effect=copy.deepcopy(result['effect']))) is not True:
                    raise OSError('effect output not confirmed flushed')
                result['effect_output_flushed']=True
            except Exception as exc:
                result['effect_publication_error']=dict(type=type(exc).__name__,message=str(exc))
            result['effect_publish_finished_ns']=time.perf_counter_ns()
        stage = 'evaluate'
        evaluation = evaluate()
        if not isinstance(evaluation, dict) or type(evaluation.get('success')) is not bool:
            raise ValueError('evaluation must contain boolean success')
        result['evaluation'] = copy.deepcopy(evaluation)
        stage = 'publish'
        message=dict(event='independent_evaluation', final_program=program_id, **evaluation)
        if 'effect' in result:message['effect']=copy.deepcopy(result['effect'])
        if publish(message) is not True:
            raise OSError('evaluation output not confirmed flushed')
        result['output_flushed'] = True
        result['status'] = 'finished' if 'effect_publication_error' not in result else 'finalization_error'
        if 'effect_publication_error' in result:result['failure_stage']='publish_effect'
    except Exception as exc:
        result.update(status='finalization_error', failure_stage=stage,
                      error=dict(type=type(exc).__name__, message=str(exc)))
    result['finished_ns'] = time.perf_counter_ns()
    return result
