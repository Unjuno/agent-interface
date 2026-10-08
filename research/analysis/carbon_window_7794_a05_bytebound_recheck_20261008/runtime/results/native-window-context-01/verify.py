"""Read-only archive, native receipt, window context and saved-file verification."""
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import runpy
import xml.etree.ElementTree as ET
import zipfile


def main():
    here = Path(__file__).resolve().parent
    read_archive = runpy.run_path(str(here.parent/'native-primary-review-01/verify.py'))['read_archive']
    data = read_archive(here, 'evidence.tar.gz', 'manifest.json')
    summary = json.loads((here/'summary.json').read_text())
    for run in summary['runs']:
        prefix = run['name']+'/'
        def read(name):
            return json.loads(data[prefix+name])
        metadata = [json.loads(raw) for name,raw in data.items()
                    if name.startswith(prefix) and '/' not in name[len(prefix):] and name.endswith('-metadata.json')]
        images = [m for m in metadata if m.get('image_status') == 'image']
        statuses = Counter()
        for response in images:
            inventory = response['window_inventory']
            statuses[inventory['status']] += 1
            assert inventory['authority'] == 'none'
            if inventory['status'] == 'recorded':
                raw = data[prefix+f"allocation/run/windows-{inventory['stage']}.json"]
                assert hashlib.sha256(raw).hexdigest() == inventory['source']['sha256']
                assert json.loads(raw) == inventory['text']
            ref = response['image_reference']
            raw = data[ref['path'].split('/results-local/',1)[1]]
            assert hashlib.sha256(raw).hexdigest() == ref['sha256']
        assert dict(statuses) == run['inventory_statuses']
        if run['name'].endswith('-02'):
            assert statuses == {'recorded':6}
            modal = read('action-4-metadata.json')
            assert 'Confirm File Format' in modal['window_inventory']['text']
            assert modal['continuation']['stage'] == modal['window_inventory']['stage'] == 5
        else:
            assert statuses == {'recorded':2, 'unavailable':5}
        requests = [json.loads(raw) for name,raw in data.items()
                    if name.startswith(prefix) and '/' not in name[len(prefix):] and name.endswith('-request.json')]
        assert Counter(r['tool'] for r in requests) == run['tool_calls']
        actions = read('allocation/run/actions.json')
        assert len(actions) == run['guarded_actions'] == 4
        for action in actions:
            assert action['result']['status'] == 'completed'
            release = action['result']['execution']['releases'][-1]
            assert release['verified'] and not release['keys_down'] and not release['buttons_down']
        terminal = [m['allocation'] for m in metadata if m.get('allocation',{}).get('status') == 'terminal']
        assert len(terminal) == 1 and terminal[0]['returncode'] == 0
        assert terminal[0]['task_success'] is None
        evaluation = read('allocation/run/evaluation.json')
        assert evaluation['success'] and all(v['success'] for v in evaluation['applications'].values())
        for filename, digest in run['saved_readback']['hashes'].items():
            assert hashlib.sha256(data[prefix+'allocation/run/'+filename]).hexdigest() == digest
        # Independent persisted-state parser; no running application or evaluator API.
        with zipfile.ZipFile(io.BytesIO(data[prefix+'allocation/run/sheet.xlsx'])) as workbook:
            sheet = ET.fromstring(workbook.read('xl/worksheets/sheet1.xml'))
        ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        values = {c.attrib['r']:c.find('s:v',ns).text for c in sheet.findall('.//s:c',ns) if c.find('s:v',ns) is not None}
        assert values['A1'] == '858' and values['A2'] == '326'
        svg = ET.fromstring(data[prefix+'allocation/run/shape.svg'])
        rect = next(svg.iter('{http://www.w3.org/2000/svg}rect'))
        assert float(rect.get('x')) > 50.5 and rect.get('transform') is None
        assert all(abs(float(rect.get(k))-v) < .1 for k,v in [('y',50),('width',40),('height',30)])
        cleanup = read('allocation/run/cleanup-report.json')
        assert cleanup['tracked_processes_terminal'] and not cleanup['descendants_verified']
        print(json.dumps({'run':run['name'], 'window_context':dict(statuses),
                          'saved_calc':[858,326], 'saved_svg':dict(rect.attrib),
                          'guarded_actions_with_verified_release':4}))
    assert json.loads(data['native-window-context-ci-01/result.json'])['status'] == 'PASS'
    print(json.dumps({'files':len(data), 'scope':'scoped two-app saved effects and context delivery; no speed/token claim'}))


if __name__ == '__main__':
    main()
