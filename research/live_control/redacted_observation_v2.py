"""Pixel withholding with explicit half-open geometry and unknown semantics."""
import copy
import json
from pathlib import Path

from PIL import Image, ImageDraw


def validate_policy(policy, width, height):
    if type(policy) is not dict or set(policy) != {
            'policy_id', 'version', 'mode', 'regions', 'retention'}:
        raise ValueError('exact observation policy required')
    if (type(policy['policy_id']) is not str or not 1 <= len(policy['policy_id']) <= 128 or
            type(policy['version']) is not int or policy['version'] < 1 or
            policy['mode'] != 'OMIT_WITH_UNKNOWN' or
            policy['retention'] not in ('raw_local_only', 'presented_only')):
        raise ValueError('invalid observation policy identity or mode')
    if type(policy['regions']) is not list or not 1 <= len(policy['regions']) <= 16:
        raise ValueError('1..16 redaction regions required')
    result = copy.deepcopy(policy)
    for region in result['regions']:
        if type(region) is not dict or set(region) != {'box', 'class', 'reason'}:
            raise ValueError('exact redaction region required')
        box = region['box']
        if (type(box) is not list or len(box) != 4 or
                any(type(value) is not int for value in box)):
            raise ValueError('integer [left,top,right,bottom] required')
        left, top, right, bottom = box
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError('redaction box outside image')
        if (type(region['class']) is not str or not 1 <= len(region['class']) <= 64 or
                region['reason'] != 'REDACTED_BY_POLICY'):
            raise ValueError('bounded class and explicit policy reason required')
    return result


def render(source, destination, policy, *, source_observation_id):
    if type(source_observation_id) is not str or not 1 <= len(source_observation_id) <= 128:
        raise ValueError('bounded source observation identity required')
    source, destination = Path(source), Path(destination)
    with Image.open(source) as opened:
        image = opened.convert('RGB')
    policy = validate_policy(policy, image.width, image.height)
    draw = ImageDraw.Draw(image)
    presented = []
    for index, region in enumerate(policy['regions']):
        box = tuple(region['box'])
        # Policy boxes are [left, top, right, bottom): PIL rectangles are
        # inclusive, so translate the right and bottom edges explicitly.
        pil_box = (box[0], box[1], box[2] - 1, box[3] - 1)
        draw.rectangle(pil_box, fill=(96, 96, 96), outline=(0, 0, 0), width=2)
        # Pattern depends only on public geometry/index, never on removed pixels.
        for x in range(box[0] + 4 + index % 2, box[2] - 2, 8):
            draw.line((x, box[1] + 3, x, box[3] - 3), fill=(150, 150, 150), width=2)
        presented.append({
            'region_id': f'redacted-{index + 1}', 'box': list(box),
            'box_semantics': 'LEFT_TOP_INCLUSIVE_RIGHT_BOTTOM_EXCLUSIVE',
            'class': region['class'], 'availability': 'REDACTED_BY_POLICY',
            'evidence_removed': ['pixel_content', 'text_content'],
            'coordinate_mapping': 'unchanged_source_pixels',
            'action_policy': 'REQUIRE_AUTHORIZED_REFINEMENT',
        })
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise ValueError('presented artifact already exists')
    image.save(destination, format='PNG', compress_level=1)
    return {
        'format': 'presented-observation-v2',
        'source_observation_id': source_observation_id,
        'dimensions': [image.width, image.height],
        'policy': {'policy_id': policy['policy_id'], 'version': policy['version'],
                   'mode': policy['mode']},
        'redacted_regions': presented,
        'unavailable_semantics': 'redacted content is unknown, not absent',
        'authority': 'none',
        'input_restriction': ('do not target, transcribe, verify, or infer content '
                              'whose required evidence intersects a redacted region'),
        'raw_history_access': 'not_presented_to_planner',
    }


def full_view(source, *, source_observation_id):
    source = Path(source)
    with Image.open(source) as image:
        dimensions = [image.width, image.height]
    return {
        'format': 'presented-observation-v2',
        'source_observation_id': source_observation_id,
        'dimensions': dimensions,
        'policy': {'policy_id': 'full-control', 'version': 1, 'mode': 'FULL'},
        'redacted_regions': [], 'unavailable_semantics': None,
        'authority': 'none', 'input_restriction': None,
        'raw_history_access': 'current image only',
    }


def encoded(view):
    return json.dumps(view, sort_keys=True, separators=(',', ':'), allow_nan=False)
