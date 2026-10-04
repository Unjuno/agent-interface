from __future__ import annotations
import hashlib, json
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'research/live_control/results/recovery-assistant-01'
OUT = Path(__file__).resolve().parent / 'RESULT.json'
EXPECTED_INPUT_HASHES = {
    'events.jsonl': 'dce77e649e42541450c37caf99f8a5dc1335f7f5a21c266e2ecbddd29197e40b',
    'audit.json': '87cc4f32764e78117e71c22e9ac6b2adf511a2ebbf49ace1ce9e956050e8720e',
    'owner-events.json': 'f480dfaa3f27447a37dc5932df52d7925363aa25e88571f3ac558baa27bf05aa',
}
EXPECTED = {6: (39622963779, True), 7: (55657545885, True), 8: (62703365854, False), 9: (71260437116, True)}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def main():
    for name, expected_hash in EXPECTED_INPUT_HASHES.items():
        assert sha(SOURCE / name) == expected_hash, f'input hash mismatch: {name}'
    manifest = Path(__file__).resolve().parent / 'SHA256SUMS'
    for line in manifest.read_text(encoding='ascii').splitlines():
        expected_hash, rel = line.split('  ', 1)
        assert sha(manifest.parent / rel) == expected_hash, f'manifest hash mismatch: {rel}'
    events = [json.loads(line) for line in (SOURCE / 'events.jsonl').read_text(encoding='utf-8').splitlines() if line]
    frames = {e['sequence']: e for e in events if e.get('event') == 'observation'}
    selected = []
    for sequence, (ready_ns, focus_match) in EXPECTED.items():
        e = frames[sequence]
        assert e['image_ready_ns'] == ready_ns and e['focus_samples_match'] is focus_match
        p = SOURCE / f'{sequence:03}.png'
        selected.append({'sequence': sequence, 'id': e['id'], 'image_ready_ns': ready_ns,
                         'focus_samples_match': focus_match, 'window_context': e['context'],
                         'png_sha256': sha(p), 'png_bytes': p.stat().st_size})
    deltas=[]
    for a,b in zip(selected, selected[1:]):
        ia=Image.open(SOURCE / f"{a['sequence']:03}.png").convert('RGBA')
        ib=Image.open(SOURCE / f"{b['sequence']:03}.png").convert('RGBA')
        assert ia.size == ib.size
        diff=ImageChops.difference(ia,ib)
        pixels=sum(1 for px in diff.get_flattened_data() if px != (0,0,0,0))
        count=ia.width*ia.height
        deltas.append({'from_sequence':a['sequence'],'to_sequence':b['sequence'],
                       'image_ready_delta_ms':round((b['image_ready_ns']-a['image_ready_ns'])/1e6,3),
                       'different_pixels':pixels,'total_pixels':count,
                       'different_pixel_fraction':round(pixels/count,6)})
    audit=json.loads((SOURCE/'audit.json').read_text(encoding='utf-8'))
    owner=json.loads((SOURCE/'owner-events.json').read_text(encoding='utf-8'))
    assert audit['exact_frames']==9 and audit['programs']==4 and audit['task_success'] is True
    assert audit['actual']==[222,440] and audit['owner_closed_and_release_verified'] is True
    assert all(x.get('verified') and not x.get('keys_down') for x in owner)
    result={'status':'PASS','classification':'posthoc reconstruction of one exploratory assistant use',
      'inputs':{n:sha(SOURCE/n) for n in ('events.jsonl','audit.json','owner-events.json')},
      'selected_frames':selected,'adjacent_deltas':deltas,
      'scope':{'frames_in_original_audit':audit['exact_frames'],'programs':audit['programs'],
       'task_success':audit['task_success'],'actual':audit['actual'],
       'all_owner_releases_verified':True,'owner_closed_and_release_verified':True,
       'matched_comparison':False,'causal_wait_gain_established':False,
       'useful_feedback_onset_identified':False,'default_wait_or_sensor_adoption':False},
      'interpretation':'Sequence 6 had a format-dialog window in context but its image was unpainted; sequence 7 visibly painted the dialog. Sequence 8 still showed the dialog and had mismatching capture-time focus samples after the Return action. Timing intervals are image-ready timestamp differences, not causal attribution or useful-feedback latency.'}
    OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
