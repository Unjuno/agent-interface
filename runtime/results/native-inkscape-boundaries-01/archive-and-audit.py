import hashlib, json, shutil, sys, xml.etree.ElementTree as ET
from pathlib import Path

root = Path.cwd()
out = root/'runtime/results/native-inkscape-boundaries-01'
if '--existing' not in sys.argv:
    out.mkdir(exist_ok=False)
    shutil.copytree(root/'results-local/native-inkscape-boundaries-01', out/'probe')
    shutil.copytree(root/'results-local/native-inkscape-boundary-self-use-01', out/'self-use')
    (out/'source').mkdir()
    for name in ('probe_native_inkscape_boundaries_v1.py','run_native_calc_self_use_v1.py',
                 'native_handle_bridge_v1.py'):
        shutil.copyfile(root/'research/live_control'/name, out/'source'/name)
rows = json.loads((out/'probe/results.json').read_text())
allocation = json.loads((out/'probe/allocation.json').read_text())
assert len(rows) == len(allocation['cases']) == 16
for i, (row, case) in enumerate(zip(rows, allocation['cases'])):
    assert row['index'] == i and all(row[k] == v for k,v in case.items())
    folder = out/'probe'/f'case-{i:02}'
    assert row == json.loads((folder/'result.json').read_text())
    actual = ET.parse(folder/'shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect').attrib
    exact = (float(actual['x']) == 50 + 2*case['count'] and float(actual['y']) == 50
             and float(actual['width']) == 40 and float(actual['height']) == 30
             and 'transform' not in actual)
    assert row['exact'] == exact and 'error' not in row
    assert row['result']['status'] == 'completed'
    release = row['result']['execution']['releases']
    assert release and all(r['verified'] is True and r['keys_down'] == [] and r['buttons_down'] == [] for r in release)
    assert all(p['returncode'] is not None for p in row['cleanup'])
    source = json.loads((folder/'source.json').read_text())
    assert source['native']['artifact']['sha256'] == allocation['reference_sha256']
action = json.loads((out/'self-use/actions.json').read_text())
assert len(action) == 1 and action[0]['result']['status'] == 'completed'
release = action[0]['result']['execution']['releases']
assert release and all(r['verified'] is True and r['keys_down'] == [] and r['buttons_down'] == [] for r in release)
assert all(p['returncode'] is not None for p in json.loads((out/'self-use/cleanup.json').read_text()))
actual = ET.parse(out/'self-use/shape.svg').getroot().find('{http://www.w3.org/2000/svg}rect').attrib
assert all(float(actual[k]) == v for k,v in dict(x=64,y=50,width=40,height=30).items()) and 'transform' not in actual
for stage in (1,2):
    reply = json.loads((out/f'self-use/reply-{stage}.json').read_text())
    assert hashlib.sha256((out/f'self-use/request-{stage}.json').read_bytes()).hexdigest() == reply['decision_sha256']
images = {p.name:p for p in out.rglob('*.png') if p.name != 'reference.png'}
reference = json.loads((out/'probe/reference-source.json').read_text())
images[Path(reference['native']['artifact']['path']).name] = out/'probe/reference.png'
links = 0
def audit(value):
    global links
    if isinstance(value, dict):
        native = value.get('native')
        if isinstance(native, dict) and 'artifact' in native:
            a = native['artifact']
            p = images[Path(a['path']).name]
            assert hashlib.sha256(p.read_bytes()).hexdigest() == a['sha256']
            assert a['source_raw_sha256'] == native['sha256']
            assert value['capture_ns'] == native['capture_started_ns']
            links += 1
        for v in value.values(): audit(v)
    elif isinstance(value, list):
        for v in value: audit(v)
for p in out.rglob('*.json'): audit(json.loads(p.read_text()))
client = json.loads((out/'self-use/client-1.json').read_text())['exchange']
summary = dict(base='f54105e5b4f25e04d7e98caf44d57542bfdbc661',
    allocation_cases=16, after_click_50_ms_exact=sum(r['exact'] for r in rows if r['after_click_ms']==50),
    after_click_0_ms_exact=sum(r['exact'] for r in rows if r['after_click_ms']==0),
    cases_per_click_condition=8, retained_failures=[r['index'] for r in rows if not r['exact']],
    self_use=dict(count=7,expected_x=64,actual=actual,native_programs=1,
                  local_exchange_ms=(client['returned_ns']-client['started_ns'])/1e6),
    verified_image_hash_links=links, model_usage=None, helper_model_calls=0,
    environment=dict(platform='WSL Ubuntu Linux/X11/Xvfb/Openbox',inkscape='1.2.2',python='3.12.3',pillow='10.2.0'))
(out/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
if Path(__file__).resolve() != (out/'archive-and-audit.py').resolve():
    shutil.copyfile(__file__,out/'archive-and-audit.py')
print(json.dumps(summary,indent=2))
