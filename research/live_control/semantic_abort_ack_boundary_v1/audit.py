"""Raw-only independent checker. Does not import study, Tk or Xlib."""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys

EXPECTED = {
 'complete': (1, 1, 'COMPLETION_UNVERIFIED'),
 'applied': (0, 1, 'APPLICATION_ABORT_APPLIED'),
 'request_only': (1, 1, 'QUERY_EFFECT'),
 'timeout': (1, 1, 'QUERY_EFFECT'),
 'unsupported': (0, 0, 'REFUSED_UNSUPPORTED'),
 'stale_receipt': (1, 1, 'QUERY_EFFECT')}


def audit(raw, sources=None):
    errors, counts = [], {}
    def check(test, msg):
        if not test:
            errors.append(msg)
    construction = raw.get('construction') is True
    reps = 1 if construction else 3
    expected_ids = [('construction' if construction else 'formal')+f'-{r}-{s}'
                    for r in range(reps) for s in EXPECTED]
    rows = raw.get('rows', [])
    check([r.get('case') for r in rows] == expected_ids, 'case denominator/order')
    check(type(raw.get('reruns')) is int and raw['reruns'] == 0, 'reruns')
    check(raw.get('status') == 'COMPLETE', 'raw execution status')
    check(raw.get('source_hashes') == raw.get('post_source_hashes'), 'source drift')
    if sources is not None:
        check(raw.get('source_hashes') == sources, 'frozen sources')
    known_receipts = []
    for r in rows:
        cid = r.get('case', '?')
        try:
            s = r['scenario']
            callbacks, inputs, claim = EXPECTED[s]
            ready, trace = r['ready'], r['trace']
            events = [json.loads(t) for t in r['journal'].splitlines()]
            check(bool(events), cid+': journal')
            check(all(type(e['seq']) is int for e in events), cid+': sequence integer types')
            check([e['seq'] for e in events] == list(range(1, len(events)+1)), cid+': event sequence')
            check(all(type(e['at_ns']) is int and e['at_ns'] > 0 for e in events), cid+': event clock type')
            check([e['at_ns'] for e in events] == sorted(e['at_ns'] for e in events), cid+': event order')
            check(all(e['case'] == cid and e['session'] == ready['session'] and
                      e['action'] == ready['action'] and e['pid'] == ready['pid'] for e in events), cid+': identity')
            check(ready['button_release_binding'].strip() == 'tk::ButtonUp %W', cid+': class binding')
            check(ready['bindtags'][1:] == ['Button', '.', 'all'], cid+': class dispatch')
            check(ready['can_abort'] is (s != 'unsupported'), cid+': route capability')
            check(events[0]['metadata'] == ready, cid+': ready journal')
            for key, count in [('callbacks', callbacks), ('presses', inputs), ('releases', inputs)]:
                value = r['terminal']['state'][key]
                check(type(value) is int and value == count, cid+': terminal '+key)
                kind = 'callback' if key == 'callbacks' else key
                es = [e for e in events if e['kind'] == kind]
                check(len(es) == count, cid+': journal '+key)
                check(all(type(e['count']) is int for e in es), cid+': counter integer types')
                check([e['count'] for e in es] == list(range(1, count+1)), cid+': counter '+key)
            for kind in ('press_send', 'release_send'):
                check(sum(t['kind'] == kind for t in trace) == inputs, cid+': controller '+kind)
            check(r['candidate_claim_at_release'] == claim, cid+': candidate claim')
            check(r['unsafe_control_abort_claim'] is (s == 'request_only'), cid+': unsafe comparator')
            check(r['final_candidate_semantic_abort'] is (s == 'applied'), cid+': final abort claim')
            check(r['status'] == 'COMPLETE' and r['app_exit'] == 0 and type(r['app_exit']) is int,
                  cid+': process completion')
            check(type(r['xvfb_exit']) is int and r['xvfb_exit'] == 0, cid+': Xvfb exit')
            check(r['cleanup_neutral'] is True, cid+': cleanup flag')
            physical = r['physical']
            check([p['label'] for p in physical] == (['initial', 'pressed', 'terminal', 'cleanup_before', 'cleanup_after']
                  if inputs else ['initial', 'terminal', 'cleanup_before', 'cleanup_after']), cid+': physical coverage')
            for p in physical:
                check(type(p['mask']) is int and len(p['keys']) == 32 and
                      all(type(k) is int and 0 <= k <= 255 for k in p['keys']), cid+': physical types')
                check(not any(p['keys']), cid+': keys not neutral')
                check((p['mask'] & 0x1f00) == (0x100 if p['label'] == 'pressed' else 0), cid+': button state')
            img = r['capture']
            data = base64.b64decode(img['bytes_b64'], validate=True)
            check(hashlib.sha256(data).hexdigest() == img['sha256'], cid+': image hash')
            check(img['depth'] == 24 and img['image_byte_order'] == 0 and
                  any(f == {'depth':24, 'bits_per_pixel':32, 'scanline_pad':32} for f in img['formats']), cid+': pixel layout')
            check(img['roi'] == ready['roi'] and img['roi'][2:] == [8,8] and len(data) == 256, cid+': capture size')
            expected_pixel = bytes([255]*3 if callbacks else [0]*3)
            check(all(data[i:i+3] == expected_pixel for i in range(0, len(data), 4)), cid+': independent pixels')
            sends = [json.loads(t['wire']) for t in trace if t['kind'] == 'rpc_send']
            receives = [json.loads(t['wire']) for t in trace if t['kind'] == 'rpc_receive']
            check(all(type(x['rpc_id']) is int for x in sends+receives), cid+': RPC integer types')
            check([x['rpc_id'] for x in sends] == list(range(1, len(sends)+1)), cid+': RPC sequence')
            check([x['rpc_id'] for x in receives] == [x['rpc_id'] for x in sends], cid+': RPC pairing')
            check([e['request'] for e in events if e['kind']=='request'] == sends, cid+': receiver requests')
            check(all(t['wire'].endswith('\n') for t in trace if 'wire' in t), cid+': LF framing')
            # Bind every response to raw receiver state/event rather than trusting summary fields.
            ordered_rpc = [t for t in trace if t['kind'] in ('rpc_send','rpc_receive')]
            check([t['kind'] for t in ordered_rpc] == ['rpc_send','rpc_receive']*len(sends), cid+': serial RPC order')
            for req, resp in zip(sends, receives):
                if req['op'] in ('cancel_request','apply_cancel','close'):
                    kind = {'cancel_request':'cancel_received','apply_cancel':'cancel_applied','close':'close'}[req['op']]
                    matches = [e for e in events if e['kind'] == kind]
                    check(len(matches)==1 and {k:v for k,v in resp.items() if k!='rpc_id'} == matches[0], cid+': RPC event binding')
            check(r['initial'] == receives[0] and r['terminal'] == receives[-2] and
                  r['close'] == receives[-1], cid+': snapshot/close wire binding')
            check(r['close']['state'] == r['terminal']['state'], cid+': terminal/close state')
            check(all(type(t['at_ns']) is int and t['at_ns'] > 0 for t in trace), cid+': trace clock types')
            check([t['at_ns'] for t in trace] == sorted(t['at_ns'] for t in trace), cid+': trace order')
            applied = [e for e in events if e['kind'] == 'cancel_applied']
            received = [e for e in events if e['kind'] == 'cancel_received']
            check(len(received) == (1 if s in ('applied','request_only','timeout') else 0), cid+': received count')
            check(len(applied) == (1 if s in ('applied','request_only') else 0), cid+': applied count')
            if inputs:
                release_ns = next(t['at_ns'] for t in trace if t['kind']=='release_send')
                check(next(e['at_ns'] for e in events if e['kind']=='presses') < release_ns,
                      cid+': press before release')
            if s == 'applied':
                rec = r['receipt']
                check({k:v for k,v in rec.items() if k!='rpc_id'} == applied[0], cid+': receipt journal')
                check(all(rec[k] == ready[k] for k in ('session','case','action')) and
                      rec['nonce'] == ready['action']+':cancel' and rec['at_ns'] < release_ns,
                      cid+': current pre-release applied proof')
                response_time = next(t['at_ns'] for t in trace if t['kind']=='rpc_receive' and json.loads(t['wire'])==rec)
                decision = [t for t in trace if t['kind']=='decision']
                check(len(decision)==1 and decision[0]['claim']==claim and decision[0]['proof_valid'] is True
                      and rec['at_ns'] <= response_time <= decision[0]['at_ns'] < release_ns,
                      cid+': application response received before decision/release')
                known_receipts.append(rec)
            elif s == 'request_only':
                check(received[0]['at_ns'] < release_ns < applied[0]['at_ns'], cid+': delayed apply order')
                check(next(e['at_ns'] for e in events if e['kind']=='callback') < applied[0]['at_ns'],
                      cid+': late abort cannot undo callback')
            elif s == 'timeout':
                starts = [t for t in trace if t['kind']=='ack_wait_start']
                ends = [t for t in trace if t['kind']=='ack_wait_expired']
                check(len(starts)==1 and len(ends)==1 and
                      ends[0]['at_ns']-starts[0]['at_ns'] >= 30000000 and
                      ends[0]['at_ns'] < release_ns, cid+': timeout and mandatory release')
            elif s == 'stale_receipt':
                check(r['receipt'] in known_receipts and r['receipt']['session'] != ready['session'],
                      cid+': actual transplanted receipt')
            counts[s] = counts.get(s, 0) + 1
        except (KeyError, TypeError, ValueError, StopIteration, IndexError, AttributeError) as exc:
            errors.append(cid+': malformed '+repr(exc))
    return dict(decision='PASS_LIVE_ABORT_ACK_BOUNDARY_SCOPED' if not errors else 'FAIL_CONTROL_OR_INTEGRITY',
                construction=construction, errors=errors, rows=len(rows), scenario_counts=counts,
                unsafe_reporting_control='FAIL_FALSE_ABORT_CLAIM' if not errors else 'UNINTERPRETED',
                candidate_false_abort_claims=0 if not errors else None,
                model_calls=0, production_runtime_invocations=0)


def mutations(raw):
    variants = {}
    def variant(name, mutate):
        obj = copy.deepcopy(raw)
        mutate(obj)
        variants[name] = bool(audit(obj)['errors'])
    variant('missing_case', lambda x: x['rows'].pop())
    variant('duplicate_case', lambda x: x['rows'].__setitem__(-1, copy.deepcopy(x['rows'][0])))
    variant('effect_count', lambda x: x['rows'][0]['terminal']['state'].__setitem__('callbacks',0))
    variant('stale_applied_proof', lambda x: x['rows'][1]['receipt'].__setitem__('session','foreign'))
    variant('missing_release', lambda x: x['rows'][0].__setitem__('trace',[t for t in x['rows'][0]['trace'] if t['kind']!='release_send']))
    variant('false_abort_claim', lambda x: x['rows'][2].__setitem__('final_candidate_semantic_abort',True))
    variant('boolean_counter', lambda x: x['rows'][0]['terminal']['state'].__setitem__('callbacks',True))
    variant('missing_child_exit', lambda x: x['rows'][0].pop('app_exit'))
    variant('pixel_mutation', lambda x: x['rows'][0]['capture'].__setitem__('bytes_b64',base64.b64encode(bytes(256)).decode()))
    variant('held_button', lambda x: x['rows'][0]['physical'][-1].__setitem__('mask',256))
    variant('receipt_wire', lambda x: x['rows'][1]['trace'].__setitem__(
        next(i for i,t in enumerate(x['rows'][1]['trace']) if t['kind']=='rpc_receive' and 'cancel_applied' in t['wire']),
        dict(kind='rpc_receive', at_ns=1, wire='{}\n')))
    variant('late_applied_response', lambda x: next(t for t in x['rows'][1]['trace'] if t['kind']=='rpc_receive' and 'cancel_applied' in t['wire']).__setitem__('at_ns', 10**30))
    variant('terminal_wire', lambda x: x['rows'][0]['terminal'].__setitem__('button_state','disabled'))
    def bool_event(x):
        row=x['rows'][0]
        ev=[json.loads(t) for t in row['journal'].splitlines()]
        next(e for e in ev if e['kind']=='callback')['count']=True
        row['journal']=''.join(json.dumps(e)+'\n' for e in ev)
    variant('boolean_event_count', bool_event)
    return variants


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('raw')
    p.add_argument('--freeze')
    a = p.parse_args()
    raw = json.loads(Path(a.raw).read_text())
    sources = json.loads(Path(a.freeze).read_text())['sources'] if a.freeze else None
    result = audit(raw, sources)
    result['corruption_controls'] = mutations(raw) if raw.get('status') == 'COMPLETE' else {}
    if raw.get('status') != 'COMPLETE':
        result['decision'] = 'STOP_EVIDENCE_INCOMPLETE'
    result['raw_sha256'] = hashlib.sha256(Path(a.raw).read_bytes()).hexdigest()
    if not all(result['corruption_controls'].values()):
        result['errors'].append('mutation accepted')
        result['decision'] = 'FAIL_AUDITOR_CONTROL'
    print(json.dumps(result, sort_keys=True, indent=2))
    sys.exit(bool(result['errors']))
