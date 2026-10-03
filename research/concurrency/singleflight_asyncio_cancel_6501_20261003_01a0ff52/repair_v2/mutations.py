"""Copied-raw controls; never imports or invokes the candidate."""
import copy


def mutations(raw):
    values = []
    def add(name, scenario, policy, edit):
        altered = copy.deepcopy(raw)
        row = next(r for r in altered['rows'] if r['callers'] == 2 and r['scenario'] == scenario and r['policy'] == policy)
        edit(row)
        values.append((name, altered))
    def event(row, kind, actor=None):
        return next(e for e in row['events'] if e['kind'] == kind and (actor is None or e['actor'] == actor))
    def renumber(row):
        for i, e in enumerate(row['events']):
            e['seq'] = i + 1
    def remove_terminal(row):
        row['events'] = [e for e in row['events'] if e['kind'] != 'producer_cancelled']
        renumber(row)
    def swap_terminal_exit(row):
        a = row['events'].index(event(row, 'producer_return', 'p0'))
        b = row['events'].index(event(row, 'producer_exit', 'p0'))
        row['events'][a], row['events'][b] = row['events'][b], row['events'][a]
        renumber(row)
    # Seven reviewer findings; each was accepted by the original frozen auditor.
    add('reviewer-event-payload', 'stable', 'independent', lambda r: event(r, 'waiter_result', 'w0').__setitem__('payload_sha256', '0' * 64))
    add('reviewer-event-generation', 'generation_change', 'shield', lambda r: event(r, 'waiter_result', 'w0').__setitem__('generation', 2))
    add('reviewer-detach-conservation', 'stable', 'independent', lambda r: event(r, 'waiter_detach', 'w0').__setitem__('remaining', 42))
    add('reviewer-task-cancelled', 'stable', 'independent', lambda r: r['after_cleanup'][0].__setitem__('cancelled', True))
    add('reviewer-missing-producer-terminal', 'cancel_first', 'direct', remove_terminal)
    add('reviewer-waiter-error-identity', 'owner_failure', 'shield', lambda r: event(r, 'waiter_error', 'w0').__setitem__('error', 'ValueError'))
    add('reviewer-producer-exit-order', 'stable', 'independent', swap_terminal_exit)
    # Original eight control boundaries are retained as effective in-memory edits.
    altered = copy.deepcopy(raw); altered['rows'].pop(); values.append(('v1-drop-row', altered))
    altered = copy.deepcopy(raw); altered['rows'][1] = copy.deepcopy(altered['rows'][0]); values.append(('v1-duplicate-row', altered))
    add('v1-cancelled-delivery', 'cancel_first', 'shield', lambda r: r['outcomes'][0].__setitem__('status', 'DELIVERED'))
    add('v1-generation', 'stable', 'independent', lambda r: r['outcomes'][0].__setitem__('generation', 2))
    add('v1-producer-start', 'stable', 'independent', lambda r: r.__setitem__('events', [e for e in r['events'] if e['kind'] != 'producer_start']))
    add('v1-sequence-bool', 'stable', 'independent', lambda r: r['events'][0].__setitem__('seq', True))
    add('v1-cleanup-leak', 'stable', 'independent', lambda r: r['after_cleanup'][0].__setitem__('done', False))
    add('v1-payload', 'stable', 'independent', lambda r: r['outcomes'][0].__setitem__('payload_sha256', '0' * 64))
    # Adjacent identity, exact-scalar and unknown-event controls.
    add('actor-identity', 'stable', 'independent', lambda r: event(r, 'waiter_detach', 'w0').__setitem__('actor', 'outsider'))
    add('detach-bool', 'stable', 'independent', lambda r: event(r, 'waiter_detach', 'w0').__setitem__('remaining', True))
    add('producer-generation-bool', 'stable', 'independent', lambda r: event(r, 'producer_return', 'p0').__setitem__('generation', True))
    add('current-generation-bool', 'stable', 'independent', lambda r: event(r, 'waiter_result', 'w0').__setitem__('current_generation', True))
    add('producer-error-identity', 'owner_failure', 'shield', lambda r: event(r, 'producer_error', 'p0').__setitem__('error', 'ValueError'))
    add('outcome-caller-bool', 'stable', 'independent', lambda r: r['outcomes'][0].__setitem__('caller', False))
    add('cancellation-caller-bool', 'cancel_first', 'shield', lambda r: event(r, 'cancel_request').__setitem__('caller', False))
    add('unknown-event', 'stable', 'independent', lambda r: event(r, 'gate_open').__setitem__('kind', 'undocumented'))
    def move_gate(row):
        gate = event(row, 'gate_open'); row['events'].remove(gate); row['events'].insert(0, gate); renumber(row)
    add('gate-before-barrier', 'stable', 'independent', move_gate)
    def duplicate_terminal(row):
        terminal = event(row, 'producer_return', 'p0')
        row['events'].insert(row['events'].index(terminal), copy.deepcopy(terminal)); renumber(row)
    add('duplicate-producer-terminal', 'stable', 'independent', duplicate_terminal)
    assert len(values) == 25
    return values
