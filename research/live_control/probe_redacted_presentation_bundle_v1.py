"""Controls for crop, history and alternate-channel redaction bypasses."""
import copy
import hashlib
import json
from pathlib import Path

from redacted_presentation_bundle_v1 import build, validate


H = Path(__file__).resolve().parent
SOURCE = H / 'results/authorized-redacted-mutation-live-02'
R = H / 'results/redacted-presentation-bundle-controls-01'
R.mkdir(exist_ok=False)
image = SOURCE / 'presented/refined-redacted.png'
prompt = (SOURCE / 'prompt-2-refined.txt').read_text(encoding='utf-8')
view = json.loads(prompt.split('Observation: ')[1])
binding = {'observation_id': 'runtime-sequence-10',
           'policy_id': 'replace-hidden-value', 'policy_version': 3}
field = [60, 264, 248, 291]
authority = view['authority']
bundle = build(view, image, binding=binding, authority=authority)


def check(candidate, candidate_image=image, candidate_binding=binding,
          candidate_authority=authority):
    return validate(candidate, candidate_image,
                    current_binding=candidate_binding, field_box=field,
                    expected_authority=candidate_authority)


allowed = check(bundle)
assert allowed['deliver'] and allowed['reason'] == 'single_current_redacted_view'
cases = {}


def changed(name, mutate):
    candidate = copy.deepcopy(bundle)
    mutate(candidate)
    cases[name] = check(candidate)


changed('crop_only', lambda row: row['primary'].__setitem__(
    'coverage_box', [0, 0, view['dimensions'][0], 250]))
changed('full_source_channel', lambda row: row['alternate_channels'].append(
    {'kind': 'raw_source_image', 'observation_id': binding['observation_id']}))
changed('ocr_channel', lambda row: row['alternate_channels'].append(
    {'kind': 'ocr_text', 'text': 'withheld'}))
changed('ui_tree_channel', lambda row: row['alternate_channels'].append(
    {'kind': 'ui_tree', 'nodes': []}))
changed('clipboard_channel', lambda row: row['alternate_channels'].append(
    {'kind': 'clipboard', 'text': 'withheld'}))
changed('history_item', lambda row: row.__setitem__(
    'history', {'mode': 'bounded', 'items': [{'observation_id': 'old'}]}))
changed('raw_history_access', lambda row: row['primary']['view'].__setitem__(
    'raw_history_access', 'current_and_previous'))
changed('missing_redaction', lambda row: row['primary']['view'].__setitem__(
    'redacted_regions', []))
changed('view_observation', lambda row: row['primary']['view'].__setitem__(
    'source_observation_id', 'runtime-sequence-9'))
changed('bundle_policy_version', lambda row: row['binding'].__setitem__(
    'policy_version', 2))
changed('image_digest', lambda row: row['primary'].__setitem__(
    'image_sha256', '0' * 64))
changed('bundle_authority', lambda row: row.__setitem__('authority', None))
changed('view_authority', lambda row: row['primary']['view'].__setitem__(
    'authority', None))
assert all(not result['deliver'] for result in cases.values())
assert {name: result['reason'] for name, result in cases.items()} == {
    'crop_only': 'partial_primary_coverage',
    'full_source_channel': 'alternate_channel_present',
    'ocr_channel': 'alternate_channel_present',
    'ui_tree_channel': 'alternate_channel_present',
    'clipboard_channel': 'alternate_channel_present',
    'history_item': 'history_channel_present',
    'raw_history_access': 'raw_history_access_present',
    'missing_redaction': 'required_redaction_missing',
    'view_observation': 'view_binding_mismatch',
    'bundle_policy_version': 'bundle_binding_mismatch',
    'image_digest': 'presented_image_mismatch',
    'bundle_authority': 'authority_mismatch',
    'view_authority': 'view_authority_mismatch',
}
plan = {
    'source_result': str(SOURCE.relative_to(H)),
    'source_image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
    'source_prompt_sha256': hashlib.sha256(
        (SOURCE / 'prompt-2-refined.txt').read_bytes()).hexdigest(),
    'sources': {name: hashlib.sha256((H / name).read_bytes()).hexdigest()
                for name in ('redacted_presentation_bundle_v1.py',
                             'probe_redacted_presentation_bundle_v1.py')},
}
(R / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(R / 'accepted.json').write_text(json.dumps(allowed, indent=2) + '\n')
(R / 'refusals.json').write_text(json.dumps(cases, indent=2) + '\n')
result = {'accepted_current_bundle': 1, 'refused_bypass_bundles': len(cases),
          'model_calls': 0, 'gui_actions': 0}
(R / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
