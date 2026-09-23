"""Keep one unresolved OpenTTD drag effect visible across inspection turns."""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance

from openttd_contact_sheet_v1 import build as build_hover_sheet
from openttd_drag_effect_v1 import drag_box


def _runtime_image(runtime_dir, value):
    name = Path(value).name
    if not name:
        raise ValueError('runtime image name required')
    path = Path(runtime_dir) / name
    if not path.is_file():
        raise ValueError(f'runtime image unavailable: {name}')
    return path


def _observations(applied):
    return [record for record in applied['result']['reply']['records']
            if record.get('event') == 'observation']


def _new_effect(applied, drag, runtime_dir, turn):
    after = _observations(applied)
    if not after:
        raise ValueError('post-drag observation required')
    before_record = applied['fresh_observation']
    after_record = after[-1]
    before_path = _runtime_image(runtime_dir, before_record['image'])
    after_path = _runtime_image(runtime_dir, after_record['image'])
    with Image.open(before_path) as opened:
        size = opened.size
    return {
        'source_turn': turn,
        'before_image': before_path.name,
        'after_image': after_path.name,
        'before_sequence': before_record['sequence'],
        'after_sequence': after_record['sequence'],
        'crop_box': list(drag_box(drag, size)),
        'inspection_turns': 0,
    }


def _validate_effect(effect):
    required = {
        'source_turn', 'before_image', 'after_image', 'before_sequence',
        'after_sequence', 'crop_box', 'inspection_turns',
    }
    if type(effect) is not dict or set(effect) != required:
        raise ValueError('exact effect memory fields required')
    if (type(effect['source_turn']) is not int or effect['source_turn'] < 1
            or type(effect['inspection_turns']) is not int or effect['inspection_turns'] < 0
            or type(effect['before_sequence']) is not int
            or type(effect['after_sequence']) is not int
            or type(effect['before_image']) is not str
            or type(effect['after_image']) is not str
            or type(effect['crop_box']) is not list or len(effect['crop_box']) != 4
            or any(type(value) is not int for value in effect['crop_box'])):
        raise ValueError('invalid effect memory')


def build(current_image, applied, proposal, runtime_dir, destination, effect=None, turn=None):
    """Return a bounded planner sheet and the single unresolved drag memory."""
    current_image = Path(current_image)
    runtime_dir = Path(runtime_dir)
    destination = Path(destination)
    drags = [step for step in proposal.get('steps', []) if step.get('op') == 'pointer_drag']
    if len(drags) > 1:
        raise ValueError('at most one pointer_drag per planner turn')
    if drags:
        if type(turn) is not int or turn < 1:
            raise ValueError('drag source turn required')
        effect = _new_effect(applied, drags[0], runtime_dir, turn)
        base_path = current_image
    else:
        if effect is None:
            return build_hover_sheet(current_image, applied, proposal, runtime_dir, destination), None
        _validate_effect(effect)
        effect = dict(effect)
        effect['inspection_turns'] += 1
        base_path = build_hover_sheet(
            current_image, applied, proposal, runtime_dir, destination.with_suffix('.hover.png'))

    _validate_effect(effect)
    before_path = _runtime_image(runtime_dir, effect['before_image'])
    after_path = _runtime_image(runtime_dir, effect['after_image'])
    with Image.open(base_path) as opened:
        base = opened.convert('RGB')
    with Image.open(before_path) as opened:
        before = opened.convert('RGB')
    with Image.open(after_path) as opened:
        after = opened.convert('RGB')
    with Image.open(current_image) as opened:
        latest = opened.convert('RGB')
    if before.size != after.size or after.size != latest.size:
        raise ValueError('effect frame sizes differ')
    left, top, right, bottom = effect['crop_box']
    if not (0 <= left < right <= before.width and 0 <= top < bottom <= before.height):
        raise ValueError('effect crop outside frame')

    before_crop = before.crop((left, top, right, bottom))
    after_crop = after.crop((left, top, right, bottom))
    latest_crop = latest.crop((left, top, right, bottom))
    difference = ImageEnhance.Contrast(
        ImageChops.difference(before_crop, after_crop)).enhance(4.0)
    scale = min(3, max(1, base.width // (4 * before_crop.width)))
    panels = [image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
              for image in (before_crop, after_crop, latest_crop, difference)]
    row_height = 30 + max(panel.height for panel in panels)
    sheet = Image.new('RGB', (base.width, base.height + row_height), 'black')
    sheet.paste(base, (0, 0))
    draw = ImageDraw.Draw(sheet)
    x = 0
    labels = (
        f"turn {effect['source_turn']} before",
        f"turn {effect['source_turn']} after",
        f"latest inspection {effect['inspection_turns']}",
        'action difference x4',
    )
    for label, panel in zip(labels, panels):
        sheet.paste(panel, (x, base.height + 30))
        draw.text((x + 6, base.height + 8), label, fill='white')
        x += panel.width
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)
    return destination, effect
