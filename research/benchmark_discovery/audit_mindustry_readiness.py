"""Audit one development self-use episode; no resource-flow task score."""
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'observation_tiles'))
from tile_transport import Decoder

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    root = HERE / 'results/mindustry-readiness-01'
    manifest = json.loads((root / 'manifest.json').read_text())
    for path, digest in manifest['sources'].items():
        assert sha(HERE.parent / path) == digest, path
    assert sha(HERE / 'results/mindustry-reset-01/canonical.msav') == manifest['save_sha256']
    events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
    decoder = Decoder('live-control')
    observations = [r for r in events if r['event'] == 'observation']
    for n, record in enumerate(observations, 1):
        assert record['sequence'] == n
        frame = decoder.accept((root / f'{n:03d}.ait').read_bytes())
        with Image.open(root / Path(record['image']).name) as im:
            assert (im.width,im.height,im.mode,im.tobytes()) == (frame.width,frame.height,frame.mode,frame.pixels)
    accepted = [r for r in events if r['event'] == 'accepted']
    terminals = [r for r in events if r['event'] == 'terminal']
    assert [r['id'] for r in accepted] == ['resume','inspect-spawn','move-right-pause']
    assert [r['id'] for r in terminals] == [r['id'] for r in accepted]
    assert not any(r['event'] == 'rejected' for r in events)
    assert all(r['status'] == 'completed' and r['release']['verified'] is True for r in terminals)
    samples = [json.loads(line) for line in (root / 'readiness.jsonl').read_text().splitlines()]
    assert [s['sample'] for s in samples] == list(range(len(samples)))
    assert all(s['task_success'] is None for s in samples)
    first, last = samples[0], samples[-1]
    assert first['paused'] is True and first['player_dead'] is True and first['unit'] is None
    alive = [s for s in samples if s['unit'] is not None and not s['player_dead']
             and not s['unit']['dead'] and s['unit']['added']]
    assert alive and len({s['unit']['id'] for s in alive}) == 1
    assert any(not s['paused'] for s in alive)
    assert last['paused'] is True and last['player_dead'] is False
    dx = last['unit']['x'] - alive[0]['unit']['x']
    dy = last['unit']['y'] - alive[0]['unit']['y']
    assert dx > 8 and abs(dy) < 8  # post-hoc readiness sanity check, not task benchmark
    assert first['core'] == last['core']
    cleanup = json.loads((root / 'cleanup.json').read_text())
    assert cleanup['all_owned_processes_exited'] and cleanup['save_unchanged']
    programs = []
    for admission, terminal in zip(accepted,terminals):
        obs = next(r for r in observations if r['id'] == admission['id'])
        programs.append({'id':admission['id'],
            'accepted_to_first_capture_ms':(obs['capture_ns']-admission['accepted_ns'])/1e6,
            'accepted_to_first_emit_ms':(obs['emitted_ns']-admission['accepted_ns'])/1e6,
            'accepted_to_terminal_ms':(terminal['terminal_ns']-admission['accepted_ns'])/1e6})
    holds = []
    for r in events:
        if r['event']=='step_started' and r['operation']=='hold':
            end = next(e for e in events if e['event']=='step_completed' and e['id']==r['id'] and e['step']==r['step'])
            cmd = next(e['command'] for e in events if e['event']=='command' and e['command'].get('id')==r['id'])
            holds.append({'id':r['id'],'step':r['step'],
                'requested_hold_ms':cmd['steps'][r['step']]['duration_ms'],
                'whole_step_ms':(end['completed_ns']-r['issued_ns'])/1e6,
                'physical_key_down_duration_ms':None})
    report = {'scope':'one known readiness episode; no held-out score or speedup',
        'initial_player_ready':False,'resume_and_movement_observed':True,
        'oracle_samples':len(samples),'exact_frames':len(observations),
        'programs':programs,'holds':holds,'unit_dx_world':dx,'unit_dy_world':dy,
        'first_live_sample':alive[0]['sample'],'first_live_tick':alive[0]['tick'],
        'initial_tick':first['tick'],'final_tick':last['tick'],
        'initial_capture_to_final_terminal_ms':(terminals[-1]['terminal_ns']-observations[0]['capture_ns'])/1e6,
        'between_program_terminal_and_next_admission_ms':[(b['accepted_ns']-a['terminal_ns'])/1e6 for a,b in zip(terminals,accepted[1:])],
        'model_tokens':None,'model_receipt_ns':None,'task_success':None,
        'timing_scope':'Python runtime process only; Java oracle sample indices are not wall-clock timestamps',
        'audit_source_sha256':sha(Path(__file__))}
    (root / 'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    main()
