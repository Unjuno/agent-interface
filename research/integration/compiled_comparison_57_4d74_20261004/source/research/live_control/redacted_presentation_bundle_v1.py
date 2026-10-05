"""Fail closed before model delivery when a redacted view has bypass channels."""
import copy
import hashlib
from pathlib import Path


def image_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(view, image, *, binding, authority):
    dimensions = view['dimensions']
    return {
        'format': 'redacted-presentation-bundle-v1',
        'binding': copy.deepcopy(binding),
        'primary': {
            'kind': 'presented_image',
            'image_sha256': image_sha256(image),
            'coverage_box': [0, 0, dimensions[0], dimensions[1]],
            'view': copy.deepcopy(view),
        },
        'history': {'mode': 'none', 'items': []},
        'alternate_channels': [],
        'authority': copy.deepcopy(authority),
    }


def validate(bundle, image, *, current_binding, field_box,
             expected_authority):
    if type(bundle) is not dict or set(bundle) != {
            'format', 'binding', 'primary', 'history',
            'alternate_channels', 'authority'}:
        return {'deliver': False, 'reason': 'bundle_shape_mismatch'}
    if bundle['format'] != 'redacted-presentation-bundle-v1':
        return {'deliver': False, 'reason': 'bundle_format_mismatch'}
    if bundle['binding'] != current_binding:
        return {'deliver': False, 'reason': 'bundle_binding_mismatch'}
    primary = bundle['primary']
    if type(primary) is not dict or set(primary) != {
            'kind', 'image_sha256', 'coverage_box', 'view'} or \
            primary['kind'] != 'presented_image':
        return {'deliver': False, 'reason': 'primary_shape_mismatch'}
    view = primary['view']
    if type(view) is not dict or view.get('format') != 'presented-observation-v2':
        return {'deliver': False, 'reason': 'view_format_mismatch'}
    if (view.get('source_observation_id') != current_binding['observation_id'] or
            view.get('policy', {}).get('policy_id') != current_binding['policy_id'] or
            view.get('policy', {}).get('version') != current_binding['policy_version']):
        return {'deliver': False, 'reason': 'view_binding_mismatch'}
    dimensions = view.get('dimensions')
    if (type(dimensions) is not list or len(dimensions) != 2 or
            any(type(value) is not int or value <= 0 for value in dimensions)):
        return {'deliver': False, 'reason': 'invalid_dimensions'}
    if primary['coverage_box'] != [0, 0, dimensions[0], dimensions[1]]:
        return {'deliver': False, 'reason': 'partial_primary_coverage'}
    if primary['image_sha256'] != image_sha256(image):
        return {'deliver': False, 'reason': 'presented_image_mismatch'}
    if view.get('raw_history_access') != 'not_presented_to_planner':
        return {'deliver': False, 'reason': 'raw_history_access_present'}
    regions = view.get('redacted_regions')
    if type(regions) is not list or not any(
            region.get('box') == field_box and
            region.get('availability') == 'REDACTED_BY_POLICY'
            for region in regions if type(region) is dict):
        return {'deliver': False, 'reason': 'required_redaction_missing'}
    if bundle['history'] != {'mode': 'none', 'items': []}:
        return {'deliver': False, 'reason': 'history_channel_present'}
    if bundle['alternate_channels'] != []:
        return {'deliver': False, 'reason': 'alternate_channel_present'}
    if bundle['authority'] != expected_authority:
        return {'deliver': False, 'reason': 'authority_mismatch'}
    if view.get('authority') != expected_authority:
        return {'deliver': False, 'reason': 'view_authority_mismatch'}
    return {
        'deliver': True,
        'reason': 'single_current_redacted_view',
        'image_sha256': primary['image_sha256'],
        'binding': copy.deepcopy(current_binding),
    }
