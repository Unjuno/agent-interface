"""Two-phase caller with an explicit task proposal validator; v1 result format.

No retries. Transport exceptions propagate with durable pending state intact.
The caller supplies an already evaluated pixel contract; this is not a wire
validator and neither sampled context nor completion proves widget identity.
"""
from copy import deepcopy
from time import perf_counter_ns
from activation_handoff_v1 import evaluate
from calc_proposal_schema_v1 import validate


def execute(call, proposal, checked, source, *, validate_proposal=validate):
    proposal = validate_proposal(deepcopy(proposal))
    steps = proposal.get('steps', [])
    if (not steps or steps[0]['op'] != 'pointer_click' or
            any(s['op'] not in ('key', 'text', 'chord') for s in steps[1:])):
        raise ValueError('requires initial click followed by keyboard-only tail')
    report = {'format': 'phased-submit-v1', 'authority': 'none',
              'status': 'refused', 'tail_submitted': False, 'exchanges': []}

    def stop(reason):
        report['reason'] = reason
        return report

    def exchange(command):
        result = call({'command': command, 'timeout': 3})
        report['exchanges'].append(result)
        report['result'] = result
        return result

    def completed(result):
        state = result['state']
        terminal = state.get('last_resolution', {}).get('terminal', {})
        release = terminal.get('release') or {}
        return (state['pending'] is None and
                terminal.get('id') == result['request']['command']['id'] and
                terminal.get('status') == 'completed' and
                terminal.get('interruption') is None and
                terminal.get('steps_completed') == len(result['request']['command']['steps']) and
                release.get('verified') is True and
                release.get('keys_down') == [] and release.get('buttons_down') == [])

    def clock():
        result = exchange({'op': 'clock'})
        if result['state']['pending'] is not None:
            return None
        return result['state']['last_resolution'].get('clock')

    if checked.get('eligible') is not True:
        return stop('target_refused')
    activation_steps = [steps[0], {'op': 'observe'}]
    activation = exchange({'op': 'submit',
                           'expected_sequence': checked['expected_sequence'],
                           'valid_until_ns': checked['valid_until_ns'],
                           'steps': activation_steps})
    report['activation'] = activation
    if not completed(activation):
        return stop('activation_unresolved_or_interrupted')
    if len(steps) == 1:
        report['status'] = 'completed'
        return report
    started = perf_counter_ns()
    c = clock()
    if c is None:
        return stop('handoff_clock_unresolved')
    sample = exchange({'op': 'submit', 'expected_sequence': c['sequence'],
                       'valid_until_ns': c['runtime_ns'] + 3_000_000_000,
                       'steps': [{'op': 'observe'}]})
    if not completed(sample):
        return stop('handoff_observation_unresolved_or_interrupted')
    c = clock()
    if c is None:
        return stop('handoff_clock_unresolved')
    fresh = sample['state']['continuation']['observation']
    gate = evaluate(activation['request']['command']['id'], activation_steps,
                    activation['state']['last_resolution']['terminal'],
                    source, fresh, c)
    report['handoff'] = {'source': source, 'fresh': fresh, 'clock': c,
                         'verdict': gate,
                         'elapsed_s': (perf_counter_ns() - started) / 1e9}
    if not gate['eligible']:
        return stop('handoff_refused')
    # durable_submit creates a distinct ID and persists pending before sending.
    report['tail_submitted'] = True
    tail = exchange({'op': 'submit', 'expected_sequence': gate['expected_sequence'],
                     'valid_until_ns': c['runtime_ns'] + 2_000_000_000,
                     'steps': steps[1:] + [{'op': 'observe'}]})
    if not completed(tail):
        return stop('tail_unresolved_or_interrupted')
    report['status'] = 'completed'
    return report
