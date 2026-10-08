"""Read archived data only. Never extract/import/run the archived harness."""
import base64
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


def require(value, reason):
    if not value:
        raise ValueError(reason)


def verify(root):
    manifest = json.loads((root / 'manifest.json').read_bytes())
    archive = root / 'evidence.zip'
    sha = lambda data: hashlib.sha256(data).hexdigest()
    require(sha(archive.read_bytes()) == manifest['archive_sha256'], 'archive digest')
    with zipfile.ZipFile(archive) as source:
        names = source.namelist()
        require(len(names) == len(set(names)), 'duplicate archive member')
        require(set(names) == set(manifest['files']), 'archive membership')
        require(sum(i.file_size for i in source.infolist()) < 64 * 1024 * 1024, 'archive size')
        files = {name: source.read(name) for name in names}
    for name, digest in manifest['files'].items():
        require(sha(files[name]) == digest, name)
    def read(name):
        return json.loads(files[name])
    for name, digest in read('run/FREEZE.json').items():
        require(sha(files['run/' + name.replace('\\', '/')]) == digest, 'freeze: ' + name)
    require(sha(files['run/FREEZE.json']) ==
            '87f7ded16bba99ec56fd6f838b1569586382b35ed9c2e2c1a902bd8fb93975bf', 'published freeze')
    sources = read('source-manifest.json')
    require(sources['revision'] == '55427ecda1474b43d8a58bbc5714de7285cc8390', 'source revision')
    for name, digest in sources['files'].items():
        require(sha(files['source/' + name.replace('\\', '/')]) == digest, 'source: ' + name)
    plan = read('run/PLAN.json')
    report = read('run/RESULT.json')
    require(report == json.loads((root / 'RESULT.json').read_bytes()), 'published report')
    require([(r['wait_ms'], r['a'], r['b']) for r in plan['rows']] ==
            [(50, 11, 13), (250, 11, 13), (250, 17, 19), (50, 17, 19)], 'frozen schedule')
    ns = {'t': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
          'o': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
    checked = []
    for spec, recorded in zip(plan['rows'], report['rows'], strict=True):
        prefix = f"run/row-{spec['row']}/"
        declaration = read(prefix + 'primary-declaration.json')
        labels = ['initial', 'action-1'] + (['action-2'] if declaration['extra_observations'] else [])
        require(declaration['extra_observations'] in (0, 1), 'observation bound')
        require(sorted(n[len(prefix):].split('-stdout.json')[0] for n in files
                       if n.startswith(prefix) and n.endswith('-stdout.json')) == sorted(labels), 'response count')
        for label in labels:
            response = read(prefix + label + '-stdout.json')
            raw = read(prefix + 'attempts/' + label + '/report.json')
            require(response['receipt']['source']['raw_report'] == raw, 'retained raw response')
            png = base64.b64decode(response['image']['data'], validate=True)
            require(png == files[prefix + label + '.png'], 'PNG equality')
            require(sha(png) == response['image_reference']['sha256'], 'PNG digest')
            if label != 'action-1':
                require(raw['input_dispatched'] is False, 'read-only observation')
        raw = read(prefix + 'attempts/action-1/report.json')
        execution = raw['result']['execution']
        require(raw['result']['status'] == 'completed', 'action status')
        require(all(r['verified'] is True and not r['keys_down'] and not r['buttons_down']
                    for r in execution['releases']) and bool(execution['releases']), 'recorded release')
        wait = execution['waits'][-1]
        require(wait['requested_ms'] == spec['wait_ms'] and wait['kind'] == 'fixed_delay'
                and wait['update_observed'] is None, 'wait semantics')
        requested = read(prefix + 'prepared-request.json')['arguments']['program']
        actual = raw['compilation']['source_program']
        actual['authority']['expires_at_ns'] = requested['authority']['expires_at_ns']
        require(actual == requested, 'only private lease timestamp may change')
        cells = ET.fromstring(files[prefix + 'invoice.fods']).findall('.//t:table-row', ns)[1].findall('t:table-cell', ns)[:3]
        values = [c.get('{' + ns['o'] + '}value') for c in cells]
        expected = [spec['a'], spec['b'], spec['a'] * spec['b']]
        require(values == list(map(str, expected)), 'saved operands/value')
        require(cells[2].get('{' + ns['t'] + '}formula') == 'of:=[.B2]*[.A2]', 'saved formula')
        require(declaration['complete'] is True and declaration['visible'] == expected, 'recorded primary declaration')
        timing = read(prefix + 'action-1-timing.json')
        require(recorded['cli_roundtrip_ms'] == (timing['ended_ns'] - timing['started_ns']) / 1e6, 'CLI timing')
        require(recorded['runtime_ms'] == (execution['ended_ns'] - execution['started_ns']) / 1e6, 'runtime timing')
        require(recorded['actual_final_wait_ms'] == (wait['ended_ns'] - wait['started_ns']) / 1e6, 'wait timing')
        require(recorded['extra_observations'] == declaration['extra_observations'], 'observation summary')
        require(sha(files[prefix + 'initial.png']) == 'b632a29a90af1cfd2f43f18d180751686bcc490242939ab3299b6617a96785f1', 'initial pixels')
        state = read(prefix + 'container-state.json')
        require(state['Status'] == 'exited' and state['ExitCode'] == 0, 'recorded container exit')
        cleanup = read(prefix + 'cleanup.json')
        require(all(not p['remaining_member_paths'] for p in cleanup['tracked_processes']), 'recorded tracked cleanup')
        checked.append({'row': spec['row'], 'saved_correct': True, 'extra_observations': declaration['extra_observations']})
    require(report['decision'] == 'HOLD_PRODUCTION_ADOPTION', 'adoption disposition')
    return {'status': 'PASS_RETAINED_RECORD_CONSISTENCY', 'files': len(files), 'rows': checked,
            'scope': 'hashes and recorded data only; not independent model viewing, live cleanup or latency proof'}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent), indent=2))
