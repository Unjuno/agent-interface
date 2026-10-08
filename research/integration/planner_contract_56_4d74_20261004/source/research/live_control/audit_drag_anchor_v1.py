"""Recompute diagnostic pixels, pointer samples and independent saved geometry."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from session_v4 import Decoder
from report_pages_v2 import digest
from score_drag_v1 import score

HERE = Path(__file__).resolve().parent
rows = []
for folder, arms in [('drag-anchor-01', ['coarse', 'fine_start']),
                     ('cause-drag-feedback-01', ['visual_correction'])]:
    root = HERE / 'results' / folder
    plan = json.loads((root / 'plan.json').read_text())
    for name, sha in plan['sources'].items():
        assert digest((HERE / name).read_bytes()) == sha
    for arm in arms:
        out = root / arm
        report = json.loads((out / 'report.json').read_text())
        assert report['execution_completed']
        assert all(v == 'close returned' for v in report['cleanup'].values())
        assert report['task_score'] == score(out / 'shape.svg')
        observations = [e for e in report['events'] if e['event'] == 'observation']
        decoder = Decoder('live-control')
        for i, event in enumerate(observations, 1):
            assert event['sequence'] == i
            frame = decoder.accept((out / f'{i:03d}.ait').read_bytes())
            with Image.open(out / Path(event['image']).name) as im:
                assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
        phase_rows = []
        for phase in report['phases']:
            assert phase['observation'] in observations
            with Image.open(out / Path(phase['observation']['image']).name) as im:
                crop = np.asarray(im)[300:550, 530:775]
                ys, xs = np.where((crop[:, :, 0] > 240) & (crop[:, :, 1] < 20) & (crop[:, :, 2] < 20))
                box = [int(xs.min()) + 530, int(ys.min()) + 300, int(xs.max()) + 530, int(ys.max()) + 300]
            assert box == phase['red_bbox']
            state = phase['state']
            held = phase['phase'] != 'released'
            assert state['owned_buttons'] == ([1] if held else [])
            assert bool(state['physical_pointer_mask'] & 256) == held
            assert state['sample_finished_ns'] <= phase['observation']['capture_ns']
            phase_rows.append({'phase': phase['phase'], 'pointer': state['pointer'], 'bbox': box})
        assert all(e['release']['verified'] for e in report['events'] if e['event'] == 'terminal')
        if arm == 'visual_correction':
            assert report['visual_correction']['residual_pixels'] == 10
            assert report['task_score']['success']
        else:
            assert not report['task_score']['success']
        rows.append({'arm': arm, 'exact_frames': len(observations), 'task_score': report['task_score'], 'phases': phase_rows})
result = {'audit_passed': True, 'audit_sha256': digest(Path(__file__).read_bytes()), 'rows': rows,
          'limits': 'Pointer sample precedes capture, not atomic held proof. Diagnostic subclass adds observations/correction outside public path semantics; no model-use, speed or generalization claim.'}
(HERE / 'results/cause-drag-feedback-01/audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
