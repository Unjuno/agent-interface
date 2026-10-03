"""Independent raw-only saved-effect, chronology and native identity audit."""
import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import tempfile

ARTIFACTS = {'case.json', 'consumer.events.jsonl', 'consumer.stderr', 'document.html',
             'owner.events.jsonl', 'owner.stderr', 'text.txt', 'window.png', 'xvfb.stderr'}
NEUTRAL = '00' * 32


def same(a, b):
    return json.dumps(a, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(b, sort_keys=True, separators=(',', ':'), allow_nan=False)


def integer(value, positive=False):
    return type(value) is int and value >= (1 if positive else 0)


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.body = False; self.paragraph = 0; self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag == 'body': self.body = True
        if self.body and tag == 'p': self.paragraph += 1
    def handle_endtag(self, tag):
        if tag == 'p': self.paragraph -= 1
        if tag == 'body': self.body = False
    def handle_data(self, data):
        if self.body and self.paragraph > 0: self.parts.append(data)


def inspect(raw, cases, root):
    errors, findings = [], []
    def need(condition, label):
        if not condition: errors.append(label)
    try:
        need(raw['schema'] == 'clipboard36-availability-v1' and raw['status'] == 'RECORDED', 'raw/status')
        need(raw['construction'] is False, 'raw/formal-type')
        need(len(raw['rows']) == len(cases) == 6, 'raw/denominator')
        for row, case in zip(raw['rows'], cases):
            cid, state, policy = case['id'], case['owner_state'], case['policy']
            need(row['id'] == cid and same(row['case'], case) and row['status'] == 'RECORDED', cid + '/case')
            folder = root / cid
            need(same(json.loads((folder / 'row.json').read_text()), row), cid + '/row-join')
            need(set(row['artifact_sha256']) == ARTIFACTS, cid + '/artifact-set')
            for name, digest in row['artifact_sha256'].items():
                need(hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest, cid + '/artifact/' + name)
            need(same(json.loads((folder / 'case.json').read_text()), case), cid + '/case-artifact')
            need((folder / 'window.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), cid + '/png')
            pids = row['pids']
            need(set(pids) == {'owner', 'consumer', 'xvfb'} and all(integer(v, True) for v in pids.values()) and len(set(pids.values())) == 3, cid + '/pids')
            need(same(row['exits'], {'consumer': 0, 'owner': 0, 'xvfb': 0}), cid + '/exits')
            need(row['owner_ready']['platform'] == row['consumer_ready']['platform'] == 'xcb', cid + '/platform')
            window = row['consumer_ready']['window']; need(integer(window, True), cid + '/window')
            for name in ['baseline', 'admission', 'before_input', 'deadline_server', 'effect_server', 'cleanup_server']:
                value = row[name]
                need(integer(value['at_ns'], True) and integer(value['owner']) and integer(value['focus']), cid + '/snapshot-types/' + name)
                need(value['keymap_hex'] == NEUTRAL, cid + '/neutral/' + name)
                if name != 'cleanup_server': need(value['focus'] == window, cid + '/focus/' + name)
            owner = row['baseline']['owner']; need(integer(owner, True), cid + '/baseline-owner')
            need(row['baseline_dump'] == {'op': 'dump', 'text': ''}, cid + '/baseline-empty')
            expected_owner = 0 if state == 'absent' else owner
            need(all(row[n]['owner'] == expected_owner for n in ['admission', 'before_input', 'deadline_server', 'effect_server']), cid + '/owner-continuity')
            need(row['cleanup_server']['owner'] == 0, cid + '/owner-cleared')
            admit = policy == 'direct' or state == 'healthy'
            need(row['admitted'] is admit, cid + '/admission-bool')
            expected_text = case['plain'] if state == 'healthy' or (state == 'stopped' and policy == 'direct') else ''
            text = (folder / 'text.txt').read_text()
            html = Text(); html.feed((folder / 'document.html').read_text())
            need(text == expected_text and ''.join(html.parts) == expected_text and row['final_dump'] == {'op': 'dump', 'text': expected_text}, cid + '/saved-effect')
            events = [json.loads(line) for line in (folder / 'consumer.events.jsonl').read_text().splitlines()]
            owner_events = [json.loads(line) for line in (folder / 'owner.events.jsonl').read_text().splitlines()]
            need(all(integer(e['monotonic_ns'], True) for e in events + owner_events), cid + '/event-clock-type')
            prefix = row['deadline_events']; need(same(events[:len(prefix)], prefix), cid + '/deadline-prefix')
            need(integer(row['deadline_ns'], True) and all(e['monotonic_ns'] <= row['deadline_ns'] for e in prefix), cid + '/deadline-clock')
            presses = [e['key'] for e in events if e['kind'] == 'key_press']
            releases = [e['key'] for e in events if e['kind'] == 'key_release']
            keys = [16777249, 86] if admit else []
            need(same(presses, keys) and same(releases, keys) and same(row['probe']['key_releases'], keys), cid + '/native-input-count')
            changes = [e for e in events if e['kind'] == 'text_changed']
            need(len(changes) == (1 if expected_text else 0) and all(e['text'] == expected_text for e in changes), cid + '/effect-count')
            commands = row['commands']; need(len(commands) == 1 + int(policy == 'read_before_input') + int(admit), cid + '/command-count')
            for cmd in commands:
                need(integer(cmd['pid'], True) and type(cmd['exit']) is int and type(cmd['timeout']) is bool and integer(cmd['start_ns'], True) and integer(cmd['end_ns'], True) and cmd['start_ns'] < cmd['end_ns'], cid + '/command-types')
            need(commands[0]['argv'] == ['xdotool', 'windowfocus', '--sync', str(window)] and commands[0]['exit'] == 0 and commands[0]['timeout'] is False, cid + '/focus-command')
            if admit:
                paste = row['paste']; need(same(paste, commands[-1]) and paste['argv'] == ['xdotool', 'key', '--clearmodifiers', 'ctrl+v'] and paste['exit'] == 0 and paste['timeout'] is False, cid + '/paste-command')
            else: need('paste' not in row, cid + '/no-paste-command')
            if policy == 'read_before_input':
                pre = row['preflight']; need(same(pre, commands[1]) and pre['argv'] == ['xclip', '-selection', 'clipboard', '-target', 'text/plain', '-out'] and pre['timeout_s'] == .5, cid + '/preflight-command')
                need(pre['timeout'] is (state == 'stopped'), cid + '/preflight-timeout')
                if state == 'healthy': need(pre['exit'] == 0 and bytes.fromhex(pre['stdout_hex']) == case['plain'].encode(), cid + '/preflight-bytes')
                elif state == 'stopped': need(pre['exit'] == -9 and pre['end_ns'] - pre['start_ns'] >= 500000000, cid + '/preflight-killed')
                else: need(pre['exit'] != 0 and pre['stdout_hex'] == '', cid + '/preflight-absent')
            else: need('preflight' not in row, cid + '/direct-no-preflight')
            if state == 'stopped':
                signals = row['signals']; need(len(signals) == 2 and same([s['signal'] for s in signals], [19, 18]) and all(type(s['signal']) is int and s['pid'] == pids['owner'] and integer(s['at_ns'], True) for s in signals), cid + '/signals')
                need(row['stopped_state'] == 'State:\tT (stopped)' and signals[0]['at_ns'] < row['admission']['at_ns'] < row['deadline_ns'] < signals[1]['at_ns'], cid + '/stopped-order')
                if policy == 'direct':
                    need(row['deadline_outcome'] == 'UNKNOWN_PENDING_EFFECT' and 'deadline_dump' not in row and integer(row['reply_start_ns'], True) and row['deadline_ns'] - row['reply_start_ns'] >= 500000000, cid + '/pending-deadline')
                    need(row['late_dump'] == {'op': 'dump', 'text': case['plain']} and integer(row['late_reply_ns'], True) and signals[1]['at_ns'] < changes[0]['monotonic_ns'] < row['late_reply_ns'], cid + '/late-effect-order')
                    need(not any(e['kind'] == 'text_changed' for e in prefix), cid + '/no-deadline-effect')
                else: need(row['deadline_outcome'] == 'REFUSED_BEFORE_INPUT', cid + '/stopped-refusal')
            else:
                need(row['signals'] == [] and 'stopped_state' not in row, cid + '/no-stop')
                need(row['deadline_outcome'] == ('REPLY' if admit else 'REFUSED_BEFORE_INPUT'), cid + '/deadline-outcome')
                if admit: need(row['deadline_dump'] == {'op': 'dump', 'text': expected_text}, cid + '/deadline-reply')
            findings.append({'id': cid, 'admitted': admit, 'deadline': row['deadline_outcome'], 'saved_text': text, 'late_effect': state == 'stopped' and policy == 'direct'})
        need(raw['environment']['cgroup'] == {'cpu.max': '50000 100000', 'memory.max': '536870912', 'pids.max': '128'}, 'environment/cgroup')
    except Exception as error:
        errors.append('unreadable:' + type(error).__name__ + ':' + str(error))
    return errors, findings


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); raw = json.loads(args.raw.read_text()); cases = json.loads(args.cases.read_text())['cases']
    errors, findings = inspect(raw, cases, args.raw.parent)
    controls = []
    edits = [
        ('window_float', 4, 'window', '/window'),
        ('pid_boolean', 0, 'pid', '/pids'),
        ('exit_boolean', 2, 'exit', '/exits'),
        ('refusal_numeric', 5, 'admitted', '/admission-bool'),
        ('late_order', 4, 'late', '/late-effect-order'),
        ('resume_before_deadline', 4, 'resume', '/stopped-order'),
        ('timeout_cleared', 5, 'timeout', '/preflight-timeout'),
        ('pending_as_complete', 4, 'pending', '/pending-deadline'),
        ('wrong_saved_text', 4, 'saved', '/saved-effect'),
        ('dropped_release', 1, 'release', '/native-input-count'),
    ]
    if not errors:
        for name, index, kind, suffix in edits:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / 'evidence'; shutil.copytree(args.raw.parent, root)
                changed = copy.deepcopy(raw); row = changed['rows'][index]; folder = root / row['id']
                if kind == 'window': row['consumer_ready']['window'] = float(row['consumer_ready']['window'])
                elif kind == 'pid': row['pids']['owner'] = True
                elif kind == 'exit': row['exits']['owner'] = False
                elif kind == 'admitted': row['admitted'] = 0
                elif kind == 'late': row['late_reply_ns'] = row['signals'][0]['at_ns']
                elif kind == 'resume': row['signals'][1]['at_ns'] = row['deadline_ns'] - 1
                elif kind == 'timeout':
                    row['preflight']['timeout'] = False; row['commands'][1]['timeout'] = False
                elif kind == 'pending':
                    row['deadline_outcome'] = 'REPLY'; row['deadline_dump'] = row['late_dump']
                elif kind == 'saved':
                    (folder / 'text.txt').write_text('Juniper'); row['final_dump']['text'] = 'Juniper'
                elif kind == 'release':
                    events = [json.loads(x) for x in (folder / 'consumer.events.jsonl').read_text().splitlines()]
                    events = [e for e in events if not(e['kind'] == 'key_release' and e['key'] == 86)]
                    (folder / 'consumer.events.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
                    row['probe']['key_releases'] = [16777249]
                row['artifact_sha256'] = {n: hashlib.sha256((folder / n).read_bytes()).hexdigest() for n in ARTIFACTS}
                (folder / 'row.json').write_text(json.dumps(row, indent=2) + '\n')
                rejected, _ = inspect(changed, cases, root)
                target = row['id'] + suffix
                controls.append({'name': name, 'target': target, 'target_rejected': target in rejected, 'errors': rejected})
                if target not in rejected: errors.append('corruption-not-specifically-rejected:' + name)
    result = {'status': 'PASS_CLIPBOARD_AVAILABILITY_BOUNDARY_SCOPED' if not errors else 'FAIL_OR_INCOMPLETE',
              'errors': errors, 'findings': findings, 'controls': controls, 'raw_sha256': hashlib.sha256(args.raw.read_bytes()).hexdigest()}
    args.output.write_text(json.dumps(result, indent=2) + '\n'); print(json.dumps(result))
    raise SystemExit(bool(errors))


if __name__ == '__main__': main()
