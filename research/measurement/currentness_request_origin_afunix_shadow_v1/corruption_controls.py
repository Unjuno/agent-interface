import copy, hashlib, json, pathlib, sys, tempfile
from auditor import audit


def write_json(path, obj):
    pathlib.Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def main(result_path, trace_path, out_path):
    base_result = json.load(open(result_path))
    base_trace = pathlib.Path(trace_path).read_bytes()
    controls = []

    def check(name, result_obj, trace_bytes):
        with tempfile.TemporaryDirectory() as td:
            rp = pathlib.Path(td) / 'result.json'
            tp = pathlib.Path(td) / 'trace.jsonl'
            write_json(rp, result_obj)
            tp.write_bytes(trace_bytes)
            z = audit(str(rp), str(tp))
            controls.append({'name': name, 'rejected': z['audit'] == 'FAIL', 'errors': z['errors']})

    r = copy.deepcopy(base_result); r['trace_sha256'] = '0' * 64; check('result_trace_digest', r, base_trace)
    r = copy.deepcopy(base_result); r['decision'] = 'FAIL_STALE_TRANSPORT_LAUNDERING'; check('decision', r, base_trace)
    r = copy.deepcopy(base_result); r['planner_generations_seen'] = [0]; check('planner_generations', r, base_trace)
    r = copy.deepcopy(base_result); r['primary_invocations'] = 2; check('primary_invocations', r, base_trace)
    r = copy.deepcopy(base_result); r['cleanup_residual_processes'] = 1; check('cleanup', r, base_trace)

    rows = [json.loads(x) for x in base_trace.splitlines() if x]
    rows2 = copy.deepcopy(rows)
    rows2[0]['outputs']['install1']['status'] = 'DECISION_INSTALLED'
    tb = b''.join((json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n').encode() for x in rows2)
    r = copy.deepcopy(base_result); r['trace_sha256'] = hashlib.sha256(tb).hexdigest(); r['trace_bytes'] = len(tb); check('trace_status_semantics', r, tb)

    rows3 = copy.deepcopy(rows)
    t = rows3[0]['timeline']; t['release_sent'] = t['ack_received'] - 1
    tb = b''.join((json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n').encode() for x in rows3)
    r = copy.deepcopy(base_result); r['trace_sha256'] = hashlib.sha256(tb).hexdigest(); r['trace_bytes'] = len(tb); check('timeline_order', r, tb)

    rows4 = copy.deepcopy(rows)
    rows4[0]['outputs']['install1']['grants_input_authority'] = True
    tb = b''.join((json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n').encode() for x in rows4)
    r = copy.deepcopy(base_result); r['trace_sha256'] = hashlib.sha256(tb).hexdigest(); r['trace_bytes'] = len(tb); check('authority_promotion', r, tb)

    out = {'controls': controls, 'rejected': sum(x['rejected'] for x in controls), 'total': len(controls)}
    assert out['rejected'] == out['total']
    write_json(out_path, out)
    print(json.dumps({'rejected': out['rejected'], 'total': out['total']}, sort_keys=True))

if __name__ == '__main__':
    main(*sys.argv[1:])
