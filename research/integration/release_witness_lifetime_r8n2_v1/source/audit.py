"""Raw-only independent reconstruction. Does not import runner, policy or Xlib."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path

SCENARIOS = ('LIVE_RELEASE', 'DESTROY_RELEASE', 'DESTROY_HELD', 'DESTROY_WITNESS_LOST')


def load_cases(paths: list[Path]) -> list[dict]:
    return [dict(raw=json.loads((p / 'RAW.json').read_text()),
                 recipient=[json.loads(s) for s in (p / 'recipient.jsonl').read_text().splitlines()],
                 witness=[json.loads(s) for s in (p / 'witness.jsonl').read_text().splitlines()],
                 driver=[json.loads(s) for s in (p / 'driver.jsonl').read_text().splitlines()]) for p in paths]


def audit(cases: list[dict], ids: list[int], source_hashes: dict) -> dict:
    errors = []
    checks = 0
    counts = collections.Counter()
    intervals = []

    def need(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(label)

    need(len(cases) == len(ids), 'case-count')
    need([c['raw']['index'] for c in cases] == ids, 'case-order')
    need(len({c['raw']['epoch'] for c in cases}) == len(cases), 'distinct-server-epochs')
    for c in cases:
        r = c['raw']
        cid = str(r['index'])
        try:
            s = SCENARIOS[r['index'] % 4]
            need(r['scenario'] == s, cid + ':scenario-binding')
            need(r['config'] == ('bare' if r['index'] % 8 < 4 else 'openbox'), cid + ':config-binding')
            need(r['repetition'] == r['index'] // 8, cid + ':repetition')
            need(r['complete'] is True and 'error' not in r, cid + ':complete')
            need(r['source_hashes'] == source_hashes, cid + ':source-binding')
            need(not r.get('cleanup_errors') and not r.get('emergency_cleanup_error'), cid + ':cleanup-errors')
            roles = {p['name']: p for p in r['processes']}
            need(set(roles) == ({'xvfb', 'recipient', 'witness', 'policy'} | ({'openbox'} if r['config'] == 'openbox' else set())), cid + ':roles')
            need(all(p['returncode'] == 0 for p in roles.values()), cid + ':exits')
            need(len({p['pid'] for p in roles.values()}) == len(roles), cid + ':independent-processes')
            code = r['keycode']
            for role in ('recipient', 'witness'):
                rows = c[role]
                need([x['seq'] for x in rows] == list(range(1, len(rows) + 1)), cid + ':' + role + ':sequence')
                need([x['time_ns'] for x in rows] == sorted(x['time_ns'] for x in rows), cid + ':' + role + ':clock')
                for row in rows:
                    need(row['epoch'] == r['epoch'] and row['actuation'] == r['actuation'] and row['pid'] == roles[role]['pid'] and row['keycode'] == code, cid + ':actor-lineage')
                need(rows[0] == r[role + '_ready'] and rows[-1]['kind'] == 'closed', cid + ':' + role + ':lifetime')
            witness_samples = [x for x in c['witness'] if x['kind'] == 'sample']
            need([x['request_id'] for x in witness_samples] == (['down'] if s == 'DESTROY_WITNESS_LOST' else ['down', 'post']), cid + ':query-count')
            need(witness_samples[0] == r['down'], cid + ':down-raw')
            for sample in witness_samples:
                bitmap = sample['keymap']
                need(len(bitmap) == 32 and all(type(v) is int and 0 <= v <= 255 for v in bitmap), cid + ':keymap-format')
                need(sample['key_down'] is bool(bitmap[code // 8] & (1 << (code % 8))), cid + ':keymap-decoding')
                need(0 < sample['query_start_ns'] <= sample['query_end_ns'] <= sample['time_ns'], cid + ':query-brackets')
            need(r['down']['key_down'] is True, cid + ':witnessed-press')
            if s == 'DESTROY_WITNESS_LOST':
                need(r['post'] is None, cid + ':no-invented-query')
            else:
                need(witness_samples[1] == r['post'], cid + ':post-raw')
                need(r['post']['query_start_ns'] > r['down']['query_end_ns'], cid + ':query-order')
                need(r['post']['key_down'] is (s == 'DESTROY_HELD'), cid + ':post-state')
            app_events = [x for x in c['recipient'] if x['kind'] == 'key_event']
            need([x['event_type'] for x in app_events] == ([2, 3] if s == 'LIVE_RELEASE' else [2]), cid + ':recipient-events')
            need(app_events == r['app_post']['events'], cid + ':app-post-reconstruction')
            need(r['app_down']['events'] == app_events[:1], cid + ':app-down-reconstruction')
            need(all(x['event_keycode'] == code and x['window'] == r['recipient_ready']['window'] and not x['send_event'] for x in app_events), cid + ':app-target-key')
            if s != 'LIVE_RELEASE':
                need(r['destroy'] in c['recipient'], cid + ':destroy-original')
                need(r['destroy']['destroy_start_ns'] >= r['down']['query_end_ns'], cid + ':destroy-after-down')
                need(r['target_exists_after_destroy'] is False and r['destroy_probe_exception'] == 'BadWindow', cid + ':destroy-query')
            ops = r['operations']
            need([x['kind'] for x in ops] == (['key_down_request', 'key_down_return', 'release_withheld_until_measurement'] if s == 'DESTROY_HELD' else ['key_down_request', 'key_down_return', 'release_request', 'release_return']), cid + ':input-ops')
            need(ops[1]['emissions'] == 1 and r['down']['query_start_ns'] >= ops[1]['time_ns'], cid + ':press-lineage')
            if s != 'DESTROY_HELD':
                need(ops[3]['emissions'] == 2 and r['backend_release']['verified'] is True, cid + ':backend-release')
                need(ops[2]['time_ns'] <= r['backend_release']['monotonic_ns'] <= ops[3]['time_ns'], cid + ':release-brackets')
                if s != 'LIVE_RELEASE':
                    need(r['destroy']['destroy_end_ns'] <= ops[2]['time_ns'], cid + ':destroy-before-release')
            for key in ('before_input', 'audit_measurement', 'final_state'):
                ob = r[key]
                need(ob['start_ns'] <= ob['end_ns'], cid + ':query-time')
                decoded = bool(ob['keymap'][code // 8] & (1 << (code % 8)))
                need(ob['key_down'] is decoded, cid + ':independent-key-bit')
                need(decoded is (key == 'audit_measurement' and s == 'DESTROY_HELD'), cid + ':independent-state')
            need(all(v == 0 for v in r['final_state']['keymap']) and r['final_state']['pointer_mask'] & 0x1f00 == 0, cid + ':final-neutral')
            need(r['fixture_cleanup_release']['verified'] is True, cid + ':fixture-cleanup')
            need(r['audit_measurement']['end_ns'] <= r['policy_completed_ns'] <= r['fixture_cleanup_started_ns'] <= r['final_state']['start_ns'], cid + ':cleanup-not-measurement')
            req = r['policy_request']
            need(set(req) == {'identity', 'before', 'after', 'app_events'}, cid + ':policy-allowlist')
            need(req['before'] == r['down'] and req['after'] == r['post'] and req['app_events'] == app_events, cid + ':policy-original-evidence')
            need(req['identity'] == dict(epoch=r['epoch'], actuation=r['actuation'], keycode=code,
                pid=roles['witness']['pid'], recipient_pid=roles['recipient']['pid'], window=r['recipient_ready']['window']), cid + ':policy-identity')
            need(json.loads(r['policy_stdin']) == req and json.loads(r['policy_stdout']) == r['policy_result'], cid + ':policy-bytes')
            want_app = 'APP_RELEASE_OBSERVED' if s == 'LIVE_RELEASE' else 'UNKNOWN'
            want_server = {'LIVE_RELEASE': 'SERVER_RELEASE_OBSERVED', 'DESTROY_RELEASE': 'SERVER_RELEASE_OBSERVED', 'DESTROY_HELD': 'STILL_DOWN', 'DESTROY_WITNESS_LOST': 'UNKNOWN'}[s]
            interval = [r['down']['query_start_ns'], r['post']['query_end_ns']] if want_server == 'SERVER_RELEASE_OBSERVED' else None
            need(r['policy_result'] == dict(app=want_app, server=want_server, release_interval_ns=interval, authority='none', task_success=None), cid + ':classification')
            if interval:
                need(interval[0] <= ops[2]['time_ns'] <= ops[3]['time_ns'] <= interval[1], cid + ':release-in-witness-interval')
                intervals.append(interval[1] - interval[0])
            for row in c['driver']:
                if row['kind'] == 'receive':
                    need(json.loads(row['payload']) in c[row['actor']], cid + ':ipc-byte-provenance')
            for row in ops:
                need(row in c['driver'], cid + ':operation-original')
            counts['app:' + want_app] += 1
            counts['server:' + want_server] += 1
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            errors.append(cid + ':malformed:' + type(exc).__name__)
    return dict(decision='PASS_RELEASE_WITNESS_LIFETIME_SCOPED' if not errors and len(ids) == 16 else ('PASS_CONSTRUCTION_AUDIT' if not errors else 'HOLD_AUDIT'), checks=checks, rows=len(cases), errors=errors, counts=dict(sorted(counts.items())), witness_interval_ns=intervals)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('root', type=Path)
    a = p.parse_args()
    paths = sorted((a.root / 'evidence').glob('case-*/RAW.json'))
    hashes = {str(x.relative_to(a.root)): hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted((a.root / 'source').rglob('*.py'))}
    result = audit(load_cases([x.parent for x in paths]), list(range(16)), hashes)
    for index, path in enumerate(paths):
        receipt_path = a.root / 'evidence' / ('launch-%02d.json' % index)
        try:
            receipt = json.loads(receipt_path.read_text())
            if receipt['returncode'] != 0 or receipt['index'] != index or receipt['started_ns'] >= receipt['ended_ns']:
                result['errors'].append('launcher:' + str(index))
            if json.loads(receipt['stdout'])['complete'] is not True or receipt['stderr']:
                result['errors'].append('launcher-output:' + str(index))
        except (OSError, KeyError, ValueError, TypeError):
            result['errors'].append('launcher-missing:' + str(index))
    freeze = json.loads((a.root / 'FREEZE.json').read_text())
    for rel, h in freeze['sha256'].items():
        if hashlib.sha256((a.root / rel).read_bytes()).hexdigest() != h:
            result['errors'].append('freeze:' + rel)
    if result['errors']:
        result['decision'] = 'HOLD_AUDIT'
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(bool(result['errors']))
