from __future__ import annotations
import time

class AuthorityEndPreconditionError(ValueError):
    pass

def build_authority_ended_receipt(
    backend,
    *,
    identifier: str,
    index: int,
    release: dict,
    steps_completed: int,
    source_sequence: int,
    lifecycle_budget_ns: int,
    post_release_input_admissions: int,
    authority_end_reason: str = 'expired',
    clock_ns=time.perf_counter_ns,
):
    if authority_end_reason != 'expired':
        raise AuthorityEndPreconditionError('v1 only admits expired authority end')
    if type(release) is not dict or release.get('verified') is not True:
        raise AuthorityEndPreconditionError('verified release required before post-authority capture')
    if release.get('keys_down') != [] or release.get('buttons_down') != []:
        raise AuthorityEndPreconditionError('empty released input state required')
    verified_ns = release.get('verified_ns')
    if type(verified_ns) is not int:
        raise AuthorityEndPreconditionError('release verified_ns required')
    if type(steps_completed) is not int or steps_completed < 0:
        raise AuthorityEndPreconditionError('nonnegative steps_completed required')
    if type(source_sequence) is not int or source_sequence < 1:
        raise AuthorityEndPreconditionError('positive source sequence required')
    if type(lifecycle_budget_ns) is not int or lifecycle_budget_ns <= 0:
        raise AuthorityEndPreconditionError('positive lifecycle budget required')
    if type(post_release_input_admissions) is not int or post_release_input_admissions != 0:
        raise AuthorityEndPreconditionError('zero post-release input admissions required')
    if type(getattr(backend, 'sequence', None)) is not int or backend.sequence != source_sequence:
        raise AuthorityEndPreconditionError('backend sequence must equal source sequence before singular capture')

    lifecycle_deadline_ns = verified_ns + lifecycle_budget_ns
    captures = 0
    error = None
    try:
        backend.snapshot(identifier, index)
        captures = 1
    except Exception as exc:
        error = repr(exc)
    snapshot_finished_ns = clock_ns()
    sequence = getattr(backend, 'sequence', None)
    sequence_advanced = type(sequence) is int and sequence > source_sequence
    post = {
        'captures': captures,
        'sequence': sequence,
        'sequence_advanced': sequence_advanced,
        'error': error,
        'grants_input_authority': False,
        'tail_program_steps_resumed': 0,
        'snapshot_finished_ns': snapshot_finished_ns,
        'lifecycle_deadline_ns': lifecycle_deadline_ns,
        'within_lifecycle_deadline': snapshot_finished_ns <= lifecycle_deadline_ns,
    }
    return {
        'terminal_status': 'authority_ended',
        'authority_end_reason': authority_end_reason,
        'release_verified': True,
        'keys_down': [],
        'buttons_down': [],
        'post_release_input_admissions': post_release_input_admissions,
        'steps_completed': steps_completed,
        'post_authority': post,
    }
