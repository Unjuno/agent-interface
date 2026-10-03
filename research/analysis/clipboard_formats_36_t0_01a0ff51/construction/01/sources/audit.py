"""Standard-library raw/saved-state oracle; imports no Qt or candidate/gates."""
import argparse
import copy
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class SavedHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_paragraph = False
        self.weights = [False]
        self.text = []
        self.bold = []

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_paragraph = True
        style = dict(attrs).get('style', '')
        match = re.search(r'font-weight\s*:\s*(\d+)', style)
        weight = (int(match.group(1)) >= 600) if match else tag in ('b', 'strong') or self.weights[-1]
        self.weights.append(weight)

    def handle_endtag(self, tag):
        if len(self.weights) > 1:
            self.weights.pop()
        if tag == 'p':
            self.in_paragraph = False

    def handle_data(self, data):
        if self.in_paragraph and data:
            self.text.append(data)
            self.bold.extend([self.weights[-1]] * len(data))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def resource(case, reference):
    plain = case['reference_plain' if reference else 'plain']
    html = case['reference_html' if reference else 'html']
    return {'generation': case['generation' if reference else 'current_generation'], 'owner': 'fixture-source' if reference else case['current_owner'], 'scope': 'private-offscreen-fixture', 'summary': sha(plain.encode()) if plain is not None else None, 'formats': [[mime, sha(value.encode())] for mime, value in [('text/plain', plain), ('text/html', html)] if value is not None]}


def independent_judgments(case, row, effect):
    expected, observed = resource(case, True), resource(case, False)
    summary = 'ELIGIBLE'
    if type(observed['generation']) is not int:
        summary = 'HOLD_RESOURCE'
    elif any(expected[key] != observed[key] for key in ('generation', 'owner', 'scope', 'summary')):
        summary = 'REJECT_DEPENDENCY'
    manifest = 'REJECT_DEPENDENCY' if summary == 'ELIGIBLE' and expected['formats'] != observed['formats'] else summary
    result = {'summary': summary, 'manifest': manifest}
    contract = case['contract']
    effect_correct = effect['text'] == contract['text'] and (contract['bold'] is None or effect['bold'] is contract['bold'])
    for arm in ('format_effect', 'effect_only'):
        if manifest != 'ELIGIBLE':
            verdict = manifest
        elif not case['paste']:
            verdict = 'NO_EFFECT'
        elif arm == 'format_effect' and len(row['requested_formats']) != 1:
            verdict = 'HOLD_FORMAT'
        elif arm == 'format_effect' and row['requested_formats'][0] not in contract['formats']:
            verdict = 'WRONG_FORMAT'
        else:
            verdict = 'VERIFIED_CORRECT' if effect_correct else 'VERIFIED_WRONG'
        result[arm] = verdict
    return result, effect_correct


def verify(packet, oracle, root):
    errors, findings = [], []
    if packet.get('schema') != 'clipboard36-qt-diagnostic-v1' or packet.get('environment', {}).get('platform_plugin') != 'offscreen':
        errors.append('schema_or_platform')
    rows = packet.get('rows', [])
    if [x.get('id') for x in rows] != [x['id'] for x in oracle['cases']]:
        return ['roster'], []
    for case, row in zip(oracle['cases'], rows):
        cid = case['id']
        # Canonical JSON retains scalar type distinctions that Python equality loses.
        for key, wanted in [('expected', resource(case, True)), ('observed', resource(case, False))]:
            if json.dumps(row.get(key), sort_keys=True) != json.dumps(wanted, sort_keys=True):
                errors.append(cid + ':' + key)
        if type(row.get('paste_attempted')) is not bool or row['paste_attempted'] != case['paste']:
            errors.append(cid + ':attempt')
        if type(row.get('format_visibility')) is not bool or row['format_visibility'] != case['format_visible']:
            errors.append(cid + ':visibility')
        formats = row.get('requested_formats')
        if type(formats) is not list or any(type(x) is not str or x not in ('text/plain', 'text/html') for x in formats) or len(set(formats)) != len(formats):
            errors.append(cid + ':format_type')
            continue
        # Fixture prediction is a recorder consistency check, not proof of consumed format.
        expected_requests = [] if not case['paste'] or not case['format_visible'] or case['plain'] is None else ['text/plain' if case['target'] in ('plain', 'prefer_plain') else 'text/html']
        if formats != expected_requests:
            errors.append(cid + ':request_trace')
        saved = {}
        for name in ('text.txt', 'document.html'):
            data = (root / cid / name).read_bytes()
            if sha(data) != row.get('saved', {}).get(name):
                errors.append(cid + ':saved_hash:' + name)
            saved[name] = data
        parser = SavedHTML()
        parser.feed(saved['document.html'].decode('utf-8'))
        effect = {'text': saved['text.txt'].decode('utf-8'), 'bold': bool(parser.bold) and all(parser.bold)}
        if ''.join(parser.text) != effect['text']:
            errors.append(cid + ':saved_text_disagreement')
        if json.dumps(row.get('qt_effect'), sort_keys=True) != json.dumps(effect, sort_keys=True):
            errors.append(cid + ':effect')
        verdicts, correct = independent_judgments(case, row, effect)
        if row.get('judgments') != verdicts:
            errors.append(cid + ':judgments')
        if row.get('planner_metadata') != row.get('observed') or 'SYNTHETIC_TOKEN_01' in json.dumps(row.get('planner_metadata')):
            errors.append(cid + ':planner_view')
        findings.append({'id': cid, 'effect_correct': correct, 'judgments': verdicts})
    return errors, findings


def mutations(packet, oracle, root):
    controls = []
    def check(name, altered):
        errors, _ = verify(altered, oracle, root)
        controls.append({'name': name, 'rejected': bool(errors), 'errors': errors})
    q = copy.deepcopy(packet); q['rows'].pop(); check('omitted_case', q)
    q = copy.deepcopy(packet); q['rows'][2]['observed']['formats'][1][1] = 'fabricated'; check('changed_html_digest', q)
    q = copy.deepcopy(packet); q['rows'][0]['observed']['generation'] = True; check('boolean_generation', q)
    q = copy.deepcopy(packet); q['rows'][4]['requested_formats'] = ['text/html']; check('fabricated_requested_format', q)
    q = copy.deepcopy(packet); q['rows'][5]['qt_effect']['bold'] = True; check('fabricated_bold_effect', q)
    q = copy.deepcopy(packet); q['rows'][6]['judgments']['format_effect'] = 'VERIFIED_CORRECT'; check('missing_format_promoted', q)
    q = copy.deepcopy(packet); q['rows'][8]['paste_attempted'] = True; check('no_paste_promoted', q)
    q = copy.deepcopy(packet); q['rows'][9]['planner_metadata']['leaked'] = 'SYNTHETIC_TOKEN_01'; check('synthetic_content_leak', q)
    q = copy.deepcopy(packet); q['rows'][0]['saved']['document.html'] = '0' * 64; check('saved_hash_corruption', q)
    q = copy.deepcopy(packet); q['rows'][7]['observed']['owner'] = 'fixture-source'; check('owner_relabel', q)
    return controls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--oracle', type=Path, required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('audit output already exists')
    packet, oracle = json.loads(args.raw.read_text()), json.loads(args.oracle.read_text())
    errors, findings = verify(packet, oracle, args.raw.parent)
    controls = mutations(packet, oracle, args.raw.parent)
    passed = not errors and all(x['rejected'] for x in controls)
    result = {'schema': 'clipboard36-independent-audit-v1', 'status': 'PASS_METHOD_SCOPED' if passed else 'FAIL_METHOD', 'raw_sha256': sha(args.raw.read_bytes()), 'errors': errors, 'findings': findings, 'mutation_controls': controls, 'consumed_format_independently_proven': False}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'rows': len(findings), 'errors': errors, 'mutations_rejected': sum(x['rejected'] for x in controls)}))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
