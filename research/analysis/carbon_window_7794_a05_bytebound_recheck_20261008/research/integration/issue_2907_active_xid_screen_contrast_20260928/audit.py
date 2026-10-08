"""Independent raw JSON/PNG audit for construction03; no runtime imports."""
import hashlib
import json
from pathlib import Path

from PIL import Image


root = Path('/evidence')
run = json.loads((root / 'run.json').read_bytes())
errors = []
expected = [
    ('baseline', [216, 34, 34]),
    ('focus_only', [216, 34, 34]),
    ('ewmh_activation', [34, 200, 68]),
]

for phase, color in expected:
    row = run.get(phase)
    if not isinstance(row, dict):
        errors.append(f'{phase}:missing_row')
        continue
    review = row.get('review')
    if phase != 'baseline' and (not isinstance(review, dict)
                                or review.get('status') != 'reviewed'
                                or review.get('authority_granted') is not False
                                or review.get('input_dispatched') is not False):
        errors.append(f'{phase}:review_gate')
    obs = row.get('observation')
    if not isinstance(obs, dict):
        errors.append(f'{phase}:missing_observation')
        continue
    path = root / Path(obs['path']).relative_to('/out')
    try:
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != obs.get('sha256') or digest != obs.get('receipt_sha256'):
            errors.append(f'{phase}:png_digest_mismatch')
        if obs.get('source_raw_sha256') != obs.get('native_sha256'):
            errors.append(f'{phase}:source_digest_mismatch')
        if obs.get('capture_ns') is None or type(obs.get('sequence')) is not int:
            errors.append(f'{phase}:capture_identity_missing')
        if obs.get('dimensions') != [800, 600]:
            errors.append(f'{phase}:dimension_mismatch')
        with Image.open(path) as opened:
            image = opened.convert('RGB')
            actual_dimensions = list(image.size)
            actual_pixel = list(image.getpixel((400, 300)))
        if actual_dimensions != [800, 600]:
            errors.append(f'{phase}:decoded_dimension_mismatch:{actual_dimensions}')
        if actual_pixel != color:
            errors.append(f'{phase}:decoded_pixel_mismatch:{actual_pixel}')
        if obs.get('sample_rgb') != actual_pixel:
            errors.append(f'{phase}:runner_audit_pixel_disagreement')
    except Exception as error:
        errors.append(f'{phase}:artifact_read:{type(error).__name__}:{error}')

calc = run.get('calc_xid')
ink = run.get('inkscape_xid')
if not (isinstance(calc, int) and isinstance(ink, int) and calc != ink):
    errors.append('distinct_window_xids')
if run.get('baseline', {}).get('active_xid') != calc:
    errors.append('baseline_active_not_calc')
if run.get('baseline', {}).get('stacking', [])[-1:] != [calc]:
    errors.append('baseline_calc_not_topmost')
if run.get('focus_only', {}).get('active_xid') != ink:
    errors.append('focus_active_not_inkscape')
if run.get('focus_only', {}).get('stacking', [])[-1:] != [calc]:
    errors.append('focus_only_raised_calc_not_retained')
focus_review = run.get('focus_only', {}).get('review', {})
if focus_review.get('observation', {}).get('pointer_binding', {}).get('surface') != ink:
    errors.append('focus_review_surface_not_requested_xid')
if run.get('ewmh_activation', {}).get('active_xid') != ink:
    errors.append('activation_active_not_inkscape')
if run.get('ewmh_activation', {}).get('stacking', [])[-1:] != [ink]:
    errors.append('activation_did_not_raise_inkscape')
activation_review = run.get('ewmh_activation', {}).get('review', {})
if activation_review.get('observation', {}).get('pointer_binding', {}).get('surface') != ink:
    errors.append('activation_review_surface_not_requested_xid')
if run.get('decision') != 'PASS_FOCUS_PIXEL_SPLIT_WITH_ACTIVATION_CONTROL':
    errors.append('runner_decision_not_expected')
if run.get('key_events') != 0 or run.get('pointer_events') != 0 or run.get('model_calls') != 0:
    errors.append('unexpected_task_input_or_model_call')
if not isinstance(run.get('cleanup'), list) or len(run['cleanup']) != 4:
    errors.append('cleanup_receipt_missing')
elif any(item.get('returncode') not in (0, -15, -9) for item in run['cleanup']):
    errors.append('cleanup_process_status')

audit = {'schema': 'issue2907/active-xid-screen-contrast-audit-v1',
         'decision': 'PASS_RAW_AUDIT' if not errors else 'FAIL_RAW_AUDIT',
         'errors': errors, 'phases_checked': len(expected),
         'source_commit': run.get('source_commit'), 'run_sha256':
             hashlib.sha256((root / 'run.json').read_bytes()).hexdigest()}
(root / 'audit.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n',
                                encoding='utf-8')
print(json.dumps(audit, sort_keys=True))
raise SystemExit(0 if not errors else 1)
