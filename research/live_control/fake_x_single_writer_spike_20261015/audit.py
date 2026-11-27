"""Saved-only auditor; no runtime imports or collector calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

MATRIX = [('coupled','healthy'), ('separated','healthy'), ('coupled','cancel'),
          ('separated','cancel'), ('coupled','expiry'), ('separated','expiry'),
          ('separated','duplicate_cancel'), ('separated','cleanup_sync_block'),
          ('separated','cleanup_emit_block'), ('separated','unknown_readback')]


def confirmed(receipt):
    return (isinstance(receipt,dict) and receipt.get('verified') is True
            and receipt.get('keys_down') == [] and receipt.get('buttons_down') == [])


def audit(row):
    errors = []
    def check(ok, label):
        if not ok: errors.append(label)
    try:
        arm, mode = row['arm'], row['mode']
        events, boundary, final = row['events'], row['boundary'], row['final']
        check((arm,mode) in MATRIX, 'KNOWN_CELL')
        check(row['errors'] == [], 'HARNESS_TERMINATED')
        check(not final['owner_alive'] and not final['observation_blocked'], 'TERMINAL_THREADS')
        check([e['n'] for e in events] == list(range(len(events))), 'EVENT_ORDER')
        selected = lambda name: [e for e in events if e['event'] == name]
        injected = selected('injected')
        cleanup = selected('cleanup_requested')
        returned = selected('cleanup_returned')
        unknown = selected('cleanup_unknown')
        revoked = selected('authority_revoked')
        check(all(e['thread_id'] == row['owner_thread_id'] for e in
                  injected+cleanup+returned+unknown+revoked+
                  selected('keymap_read')+selected('pointer_read')+selected('readback_error')), 'SINGLE_WRITER')
        check(len(cleanup) == 1, 'ONE_CLEANUP')
        check(len(returned)+len(unknown) == 1, 'ONE_CLEANUP_OUTCOME')
        check(boundary['owner_alive'] and boundary['observation_blocked'], 'NAMED_BOUNDARY')
        check(all(e['n'] >= boundary['event_count'] for e in selected('query_returned')), 'OBSERVATION_STILL_BLOCKED')
        check(len(selected('query_returned')) == 1, 'ONE_OBSERVATION_REPLY')
        positive = [e for e in injected if e['kind'] in (2,4)]
        check([(e['kind'],e['code']) for e in positive[:2]] == [(2,1),(4,1)], 'HELD_PREFIX')
        requests = selected('cancel_requested')
        check(len(requests) == (0 if mode in ('healthy','expiry') else 2 if mode == 'duplicate_cancel' else 1), 'CANCEL_COUNT')
        # Replay fake transport effects independently of the collector snapshots.
        def replay(stop):
            keys, buttons = set(), set()
            for event in injected:
                if event['n'] >= stop: continue
                kind, code = event['kind'], event['code']
                if kind == 2: keys.add(code)
                elif kind == 3: keys.discard(code)
                elif kind == 4: buttons.add(code)
                elif kind == 5: buttons.discard(code)
                else: check(False, 'KNOWN_INJECTION')
            return sorted(keys), sorted(buttons)
        for snapshot, stop in [(boundary,boundary['event_count']), (final,len(events))]:
            check((snapshot['keys'],snapshot['buttons']) == replay(stop), 'SNAPSHOT_MATCHES_EMISSIONS')
            prior_revokes = [e for e in revoked if e['n'] < stop]
            check(snapshot['revoked'] == bool(prior_revokes)
                  and snapshot['epoch'] == len(prior_revokes), 'SNAPSHOT_AUTHORITY')
            prior_outcomes = [e for e in returned+unknown if e['n'] < stop]
            expected_receipt = prior_outcomes[-1]['receipt'] if prior_outcomes else None
            check(snapshot['receipt'] == expected_receipt, 'SNAPSHOT_RECEIPT')
        check(final['keys'] == [] and final['buttons'] == [], 'TERMINAL_FAKE_NEUTRAL')
        if mode == 'healthy':
            check(not revoked and not final['revoked'] and final['epoch'] == 0, 'HEALTHY_AUTHORITY')
            check([(e['kind'],e['code']) for e in positive] == [(2,1),(4,1),(2,2),(4,3)], 'HEALTHY_TASK_PRESSES')
            admitted = selected('reply_admitted')
            check(len(admitted) == 1 and admitted[0]['proof']['epoch'] == admitted[0]['current_epoch'] == 0,
                  'FRESH_REPLY_ADMITTED')
            check(admitted[0]['n'] < positive[2]['n'] < positive[3]['n'] < cleanup[0]['n'],
                  'HEALTHY_TASK_ORDER')
        else:
            check(len(revoked) == 1 and revoked[0]['epoch'] == 1
                  and final['revoked'] and final['epoch'] == 1, 'ONE_REVOCATION')
            check(len(positive) == 2 and all(e['n'] < revoked[0]['n'] for e in positive)
                  and all(e['n'] < request['n'] for e in positive for request in requests), 'NO_LATE_PRESS')
            if mode == 'expiry':
                check(boundary['clock_ns'] == boundary['deadline_ns']
                      and all(e['clock_ns'] < boundary['deadline_ns'] for e in positive), 'ORIGINAL_DEADLINE')
            discarded = selected('reply_discarded')
            check(len(discarded) == 1 and not selected('reply_admitted')
                  and discarded[0]['proof']['epoch'] == 0
                  and discarded[0]['current_epoch'] == 1, 'STALE_REPLY_DISCARDED')
            check(revoked[0]['n'] < cleanup[0]['n'], 'REVOKE_BEFORE_CLEANUP')
            trigger = selected('clock_advanced') if mode == 'expiry' else requests
            check(bool(trigger) and trigger[0]['n'] < revoked[0]['n'], 'REQUEST_BEFORE_REVOCATION')
            check(max(e['n'] for e in returned+unknown) < discarded[0]['n'], 'CLEANUP_BEFORE_LATE_REPLY')
        releases = [e for e in injected if e['kind'] in (3,5)]
        values = [(e['kind'],e['code']) for e in releases]
        if mode == 'healthy':
            check(values[:2] == [(3,1),(3,2)] and sorted(values[2:]) == [(5,1),(5,3)]
                  and len(values) == 4, 'HEALTHY_RELEASE_ORDER')
        else:
            check(values == [(3,1),(5,1)], 'PREFIX_RELEASE_ORDER')
        check(all(e.get('cleanup') is True and e['n'] > cleanup[0]['n'] for e in releases), 'CLEANUP_RELEASE_CUSTODY')
        if returned:
            key_reads, pointer_reads = selected('keymap_read'), selected('pointer_read')
            check(len(key_reads) == len(pointer_reads) == 1
                  and key_reads[0]['keys'] == [] and pointer_reads[0]['buttons'] == []
                  and cleanup[0]['n'] < key_reads[0]['n'] < pointer_reads[0]['n'] < returned[0]['n'],
                  'FAKE_READBACK_CONFIRMS_EMPTY')
            check(all(replay(e['n'])[0] == e['keys'] for e in key_reads)
                  and all(replay(e['n'])[1] == e['buttons'] for e in pointer_reads), 'READBACK_MATCHES_EMISSIONS')
        if arm == 'coupled' or mode == 'healthy':
            check(boundary['keys'] == [1] and boundary['buttons'] == [1]
                  and boundary['receipt'] is None and not boundary['revoked'], 'COUPLED_BOUNDARY_HELD')
        elif mode in ('cancel','expiry','duplicate_cancel'):
            check(boundary['keys'] == [] and boundary['buttons'] == [], 'BOUNDARY_NEUTRAL')
            check(confirmed(boundary['receipt']) and len(returned) == 1
                  and confirmed(returned[0]['receipt'])
                  and returned[0]['n'] < boundary['event_count'], 'CLEANUP_CONFIRMED')
        elif mode in ('cleanup_sync_block','cleanup_emit_block'):
            check(boundary['receipt'] is None and boundary['revoked'], 'NO_FABRICATED_CONFIRMATION')
            held = mode == 'cleanup_emit_block'
            check(boundary['keys'] == ([1] if held else [])
                  and boundary['buttons'] == ([1] if held else []), 'BACKEND_BOUNDARY_STATE')
            resumed = row['backend_resumed']
            check(resumed is not None and resumed['observation_blocked']
                  and resumed['keys'] == [] and resumed['buttons'] == []
                  and confirmed(resumed['receipt']), 'BACKEND_RESUMED_BEFORE_OBSERVATION')
        elif mode == 'unknown_readback':
            check(boundary['keys'] == [] and boundary['buttons'] == [], 'BOUNDARY_NEUTRAL')
            check(not returned and len(unknown) == 1 and not confirmed(boundary['receipt'])
                  and final['receipt']['verified'] is False
                  and final['receipt']['state'] == 'unknown', 'UNKNOWN_IS_NOT_VERIFIED')
            check(row['pending_backend_keys'] == {'CTRL':1}
                  and row['pending_backend_buttons'] == ['left'], 'UNKNOWN_OBLIGATION_RETAINED')
        if mode != 'unknown_readback':
            check(len(returned) == 1 and confirmed(returned[0]['receipt'])
                  and confirmed(final['receipt']), 'CLEANUP_CONFIRMED')
            check(row['pending_backend_keys'] == {} and row['pending_backend_buttons'] == [], 'TRACKED_NEUTRAL')
    except (KeyError,TypeError,IndexError,AttributeError):
        errors.append('MALFORMED_OR_INCOMPLETE_TRACE')
    return sorted(set(errors))


def audit_report(report):
    errors = []
    if (report.get('scope') != 'FAKE_X_SEPARATION_SPIKE'
            or report.get('real_x_connection') is not False
            or report.get('live_allocation_invocations') != 0):
        errors.append('SCOPE')
    cases = report.get('cases',[])
    if report.get('collection_error') is not None:
        errors.append('COLLECTION_STOP')
    if [(c.get('arm'),c.get('mode')) for c in cases] != MATRIX:
        errors.append('MATRIX')
    for index, case in enumerate(cases):
        errors.extend(str(index)+':'+message for message in audit(case))
    if len(cases) >= 2:
        semantics = lambda case: [(e['kind'],e['code'],e['cleanup']) for e in case['events'] if e['event']=='injected']
        if semantics(cases[0]) != semantics(cases[1]):
            errors.append('HEALTHY_ARMS_IDENTICAL')
    return dict(disposition='PASS_FAKE_SEPARATION_NOT_PHYSICAL_BOUND' if not errors else 'INVALID_EXPOSURE', errors=errors)


def mutations(report):
    results = []
    for name in ['erased_held','fabricated_verified','late_press','second_writer','duplicate_cleanup','resurrected_reply',
                 'boundary_authority','cleanup_before_revoke','false_readback','healthy_release_order','reads_before_releases']:
        changed = copy.deepcopy(report)
        case = changed['cases'][3]
        if name == 'erased_held': changed['cases'][2]['boundary']['keys'] = []
        elif name == 'fabricated_verified': changed['cases'][7]['boundary']['receipt'] = {'verified':True,'keys_down':[],'buttons_down':[]}
        elif name == 'late_press':
            next(e for e in case['events'] if e['event'] == 'injected' and e['cleanup']).update(kind=2,code=2)
        elif name == 'second_writer': case['events'][0]['thread_id'] = -1
        elif name == 'duplicate_cleanup': case['events'].append(dict(n=len(case['events']),event='cleanup_requested',thread_id=case['owner_thread_id']))
        elif name == 'resurrected_reply': next(e for e in case['events'] if e['event'] == 'reply_discarded')['event'] = 'reply_admitted'
        elif name == 'boundary_authority': case['boundary'].update(revoked=False,epoch=0)
        elif name == 'cleanup_before_revoke':
            first = next(i for i,e in enumerate(case['events']) if e['event']=='authority_revoked')
            second = next(i for i,e in enumerate(case['events']) if e['event']=='cleanup_requested')
            case['events'][first],case['events'][second] = case['events'][second],case['events'][first]
            for n,event in enumerate(case['events']): event['n']=n
        elif name == 'false_readback': next(e for e in case['events'] if e['event']=='keymap_read')['keys']=[1]
        elif name == 'healthy_release_order':
            releases = [e for e in changed['cases'][1]['events'] if e['event']=='injected' and e['cleanup']]
            for event,(kind,code) in zip(releases,[(e['kind'],e['code']) for e in releases][::-1]):
                event.update(kind=kind,code=code)
        elif name == 'reads_before_releases':
            reads = [e for e in case['events'] if e['event'] in ('keymap_read','pointer_read')]
            retained = [e for e in case['events'] if e not in reads]
            first_release = next(i for i,e in enumerate(retained) if e['event']=='injected' and e['cleanup'])
            case['events'] = retained[:first_release]+reads+retained[first_release:]
            for n,event in enumerate(case['events']): event['n']=n
        result = audit_report(changed)
        results.append(dict(mutation=name,refused=result['disposition']=='INVALID_EXPOSURE',errors=result['errors']))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('raw',type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    raw = args.raw.read_bytes()
    report = json.loads(raw)
    result = audit_report(report)
    controls = mutations(report) if not result['errors'] else []
    freeze = Path(__file__).with_name('SOURCE_FREEZE.json').read_bytes()
    if report.get('freeze_sha256') != hashlib.sha256(freeze).hexdigest():
        result['errors'].append('FREEZE_IDENTITY')
        result['disposition'] = 'INVALID_EXPOSURE'
    result.update(raw_sha256=hashlib.sha256(raw).hexdigest(),mutation_controls=controls,
                  physical_release_bound_claimed=False)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result))
    if result['errors'] or not controls or not all(c['refused'] for c in controls):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
