"""Independent stdlib reconciliation: no candidate/app/Qt imports."""
import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

FILES = {'case.json', 'owner.events.jsonl', 'consumer.events.jsonl', 'owner.stderr',
         'consumer.stderr', 'xvfb.stderr', 'transport-plain.txt', 'transport-html.txt',
         'text.txt', 'document.html', 'window.png'}


def exact(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def integer(value, positive=False):
    return type(value) is int and value >= (1 if positive else 0)


class HTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.inside = False; self.text = []; self.bold = []

    def handle_starttag(self, tag, attrs):
        if tag in ('meta', 'link', 'br', 'img', 'hr', 'input'):
            return
        inherited = self.stack[-1][1] if self.stack else False
        match = re.search(r'font-weight\s*:\s*(\d+)', dict(attrs).get('style', ''))
        bold = int(match.group(1)) >= 600 if match else inherited or tag in ('b', 'strong')
        self.stack.append((tag, bold))
        if tag == 'p': self.inside = True

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]; break
        if tag == 'p': self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.text.append(data)
            self.bold.extend([self.stack[-1][1] if self.stack else False] * len(data))


def html_effect(data):
    parsed = HTML(); parsed.feed(data)
    return {'text': ''.join(parsed.text), 'bold': bool(parsed.bold) and all(parsed.bold)}


def verify(packet, cases, root, *, construction=False):
    errors, findings = [], []
    if packet.get('schema') != 'clipboard36-x11-transfer-v1' or packet.get('status') != 'RECORDED' or packet.get('qt_platform_required') != 'xcb' or packet.get('host_clipboard_used') is not False or packet.get('construction') is not construction:
        errors.append('packet')
    rows = packet.get('rows', [])
    if [x.get('id') for x in rows] != [x['id'] for x in cases]: return errors + ['roster'], []
    if not construction and not exact(packet.get('environment', {}).get('cgroup'), {'cpu.max': '50000 100000', 'memory.max': '536870912', 'pids.max': '128'}):
        errors.append('cgroup_observation')
    for number, (row, case) in enumerate(zip(rows, cases)):
        cid = case['id']; folder = root / cid
        def check(condition, reason):
            if not condition: errors.append(cid + ':' + reason)
        check(exact(row, json.loads((folder / 'row.json').read_text())), 'row_record')
        check(exact(case, json.loads((folder / 'case.json').read_text())), 'fixture')
        check(row.get('status') == 'RECORDED', 'status')
        check(construction or row.get('display') == ':' + str(80 + number), 'display_scope')
        check(all(row.get(role + '_ready', {}).get('platform') == 'xcb' for role in ('owner', 'consumer')), 'platform')
        pids = row.get('pids', {}); exits = row.get('exits', {})
        check(set(pids) == {'owner', 'consumer', 'xvfb'} and all(integer(x, True) for x in pids.values()) and len(set(pids.values())) == 3, 'process')
        check(set(exits) == {'owner', 'consumer', 'xvfb'} and all(type(x) is int and x == 0 for x in exits.values()), 'cleanup')
        before, after, final = [row.get(key, {}) for key in ('before', 'after', 'final')]
        owners = [x.get('clipboard_owner') for x in (before, after, final)]
        check(all(integer(x) for x in owners) and owners[0] > 0 and owners[0] == owners[1] and owners[2] == 0, 'owner')
        window = row.get('consumer_ready', {}).get('window')
        check(integer(window, True) and before.get('focus') == after.get('focus') == window and type(before.get('focus')) is int and type(after.get('focus')) is int, 'focus')
        check(all(x.get('keymap_hex') == '00' * 32 for x in (before, after, final)), 'release')
        times = [x.get('monotonic_ns') for x in (before, after, final)]
        check(all(integer(x, True) for x in times) and times == sorted(times), 'clock')
        commands = row.get('commands', [])
        expected_argv = [['xdotool', 'windowfocus', '--sync', str(window)], ['xclip', '-selection', 'clipboard', '-target', 'text/plain', '-out'], ['xclip', '-selection', 'clipboard', '-target', 'text/html', '-out'], ['xdotool', 'key', '--clearmodifiers', 'ctrl+v']]
        check([x.get('argv') for x in commands] == expected_argv and all(type(x.get('exit_code')) is int and x['exit_code'] == 0 for x in commands), 'native_command')
        for index, (mime, name, wanted) in enumerate([('text/plain', 'transport-plain.txt', case['plain']), ('text/html', 'transport-html.txt', case['html'])], 1):
            data = (folder / name).read_bytes()
            check(data == wanted.encode() and row.get('transport_sha256', {}).get(mime) == hashlib.sha256(data).hexdigest() and len(commands) > index and commands[index].get('stdout_hex') == data.hex(), 'transport:' + mime)
        for name in ('text.txt', 'document.html', 'window.png'):
            check(row.get('saved_sha256', {}).get(name) == hashlib.sha256((folder / name).read_bytes()).hexdigest(), 'saved_hash:' + name)
        artifacts = row.get('artifact_sha256', {})
        check(construction or set(artifacts) == FILES, 'record_manifest')
        for name, value in artifacts.items():
            check(name in FILES and type(value) is str and value == hashlib.sha256((folder / name).read_bytes()).hexdigest(), 'record_hash:' + name)
        owner_events = [json.loads(x) for x in (folder / 'owner.events.jsonl').read_text().splitlines()]
        consumer_events = [json.loads(x) for x in (folder / 'consumer.events.jsonl').read_text().splitlines()]
        check(all(integer(x.get('monotonic_ns'), True) and before['monotonic_ns'] <= x['monotonic_ns'] <= after['monotonic_ns'] for x in owner_events + consumer_events), 'event_clock')
        expected_mime = 'text/html' if case['target'] == 'rich' else 'text/plain'
        check(any(x.get('kind') == 'mime_request' and x.get('phase') == 'paste' and x.get('mime') == expected_mime for x in owner_events), 'paste_request')
        releases = [x.get('key') for x in consumer_events if x.get('kind') == 'key_release']
        check(exact(row.get('key_releases'), releases) and sorted(releases) == [86, 16777249] and all(type(x) is int for x in releases), 'key_release')
        check(any(x.get('kind') == 'text_changed' and x.get('phase') == 'paste' for x in consumer_events), 'effect_event')
        effect = html_effect((folder / 'document.html').read_text())
        check(effect['text'] == (folder / 'text.txt').read_text() and exact(row.get('dump'), {'op': 'dump', 'text': effect['text']}), 'saved_effect')
        expected_effect = html_effect(case['html']) if case['target'] == 'rich' else {'text': case['plain'], 'bold': False}
        check(exact(effect, expected_effect), 'native_transfer')
        reference_plain = case['plain'] if construction else 'Robin'
        reference_html = case['html'] if construction else '<p><b>Robin</b></p>'
        summary = case['plain'] == reference_plain
        manifest = summary and case['html'] == reference_html
        correct = exact(effect, {'text': reference_plain, 'bold': case['target'] == 'rich'})
        findings.append({'id': cid, 'effect': effect, 'summary_eligible': summary, 'manifest_eligible': manifest, 'effect_correct': correct})
    return errors, findings


def controls(packet, cases, root, construction=False):
    cid = cases[0]['id']; output = []
    def check(name, required, change):
        q = copy.deepcopy(packet); change(q)
        errors, _ = verify(q, cases, root, construction=construction)
        output.append({'name': name, 'required_error': required, 'rejected': required in errors, 'errors': errors})
    check('omitted_case', 'roster', lambda q: q['rows'].pop())
    check('duplicate_case', 'roster', lambda q: q['rows'].append(copy.deepcopy(q['rows'][0])))
    check('offscreen_platform', cid + ':platform', lambda q: q['rows'][0]['consumer_ready'].update(platform='offscreen'))
    check('boolean_pid', cid + ':process', lambda q: q['rows'][0]['pids'].update(owner=True))
    check('float_owner', cid + ':owner', lambda q: q['rows'][0]['before'].update(clipboard_owner=float(q['rows'][0]['before']['clipboard_owner'])))
    check('false_exit_alias', cid + ':cleanup', lambda q: q['rows'][0]['exits'].update(consumer=False))
    check('changed_focus', cid + ':focus', lambda q: q['rows'][0]['after'].update(focus=1))
    check('held_keyboard', cid + ':release', lambda q: q['rows'][0]['after'].update(keymap_hex='ff' * 32))
    check('boolean_command_exit', cid + ':native_command', lambda q: q['rows'][0]['commands'][3].update(exit_code=False))
    check('paste_command_relabel', cid + ':native_command', lambda q: q['rows'][0]['commands'][3].update(argv=['xdotool', 'key', 'ctrl+z']))
    check('missing_key_release', cid + ':key_release', lambda q: q['rows'][0].update(key_releases=[]))
    check('transport_digest_changed', cid + ':transport:text/html', lambda q: q['rows'][0]['transport_sha256'].update({'text/html': '0' * 64}))
    check('saved_html_digest_changed', cid + ':saved_hash:document.html', lambda q: q['rows'][0]['saved_sha256'].update({'document.html': '0' * 64}))
    check('dump_relabel', cid + ':saved_effect', lambda q: q['rows'][0]['dump'].update(text='fabricated'))
    return output


def main():
    parser = argparse.ArgumentParser()
    for key in ('cases', 'raw', 'output'): parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--construction', action='store_true'); args = parser.parse_args()
    if args.output.exists(): raise RuntimeError('audit output already exists')
    packet = json.loads(args.raw.read_text()); cases = json.loads(args.cases.read_text())['cases']
    errors, findings = verify(packet, cases, args.raw.parent, construction=args.construction)
    mutations = controls(packet, cases, args.raw.parent, args.construction)
    passed = not errors and all(x['rejected'] for x in mutations)
    result = {'schema': 'clipboard36-x11-transfer-audit-v1', 'status': 'PASS_X11_MIME_TRANSFER_METHOD_SCOPED' if passed else 'FAIL_X11_MIME_TRANSFER_METHOD', 'construction': args.construction,
              'raw_sha256': hashlib.sha256(args.raw.read_bytes()).hexdigest(), 'errors': errors, 'findings': findings, 'corruption_controls': mutations, 'exclusive_consumed_format_proven': False}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'errors': errors, 'rows': len(findings), 'controls': len(mutations)}))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__': main()
