"""Verify retained bytes and recorded contracts without extraction or execution."""
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_text())
comparison = json.loads((root/'comparison.json').read_text())
with tarfile.open(root/'evidence.tar.gz') as archive:
    members = archive.getmembers()
    assert len(members) == len(manifest) == 176
    assert len({m.name for m in members}) == len(members)
    data = {}
    for member in members:
        assert member.isfile() and member.name in manifest
        data[member.name] = archive.extractfile(member).read()
        assert hashlib.sha256(data[member.name]).hexdigest() == manifest[member.name]

def read(run, name):
    return json.loads(data[run+'/'+name].decode('utf-8-sig'))

decisions = []
for row in comparison:
    run = row['run']
    observe = read(run, 'action-1-metadata.json')
    reply = read(run, 'action-2-metadata.json')
    action = reply['receipt']['native_result']['action']
    feedback = action['feedback']
    assert observe['receipt']['native_result']['observation_only']['input_dispatched'] is False
    assert action['result']['status'] == 'completed'
    release = action['result']['execution']['releases'][-1]
    assert release['verified'] and release['keys_down'] == [] and release['buttons_down'] == []
    assert feedback['status'] == row['feedback'] == ('pending' if run == '01' else 'matched')
    assert len(feedback['samples']) == row['samples']
    assert (feedback['ended_ns']-feedback['started_ns'])/1e6 == row['feedback_ms']
    assert feedback['expected_title'] == row['expected_title']
    for number, response in [(1, observe), (2, reply)]:
        continuation = response['continuation']
        decision = read(run, f'decision-{number+1}.json')['arguments']
        assert continuation['status'] == 'source_available'
        assert continuation['stage'] == decision['stage']
        assert continuation['source_sequence'] == decision['decision']['source_sequence']
        assert hashlib.sha256(data[f'{run}/action-{number}.png']).hexdigest() == response['image_reference']['sha256']
    assert read(run, 'action-3-metadata.json')['outcome_summary']['evaluation_success'] is True
    assert read(run, 'action-4-metadata.json')['allocation']['returncode'] == 0
    assert read(run, 'client-exit.json')['exit_code'] == 0
    svg = data[run+'/allocation/run/shape.svg']
    assert hashlib.sha256(svg).hexdigest() == row['saved']['sha256']
    rectangle, = ET.fromstring(svg).findall('.//{http://www.w3.org/2000/svg}rect')
    actual = {k: rectangle.get(k) for k in ('x','y','width','height','transform')}
    assert actual == row['saved']['actual'] == {'x':'54','y':'50','width':'40','height':'30','transform':None}
    timings = [read(run, f'action-{i}-timing.json') for i in (1,2,3)]
    assert (timings[1]['end_ns']-timings[1]['start_ns'])/1e6 == row['action_sdk_ms']
    assert (timings[-1]['end_ns']-timings[0]['start_ns'])/1e9 == row['observe_through_finish_s']
    decision = read(run, 'decision-2.json')
    assert decision['arguments']['decision'].pop('expected_title') == row['expected_title']
    decisions.append(decision)
assert decisions[0] == decisions[1]
assert data['01/allocation/run/shape.svg'] == data['02/allocation/run/shape.svg']
print('PASS: 176 retained file hashes, action/title outcomes, saved geometry and timing accounting')
