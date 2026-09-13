"""Compose current full-frame, hover and bounded drag-effect evidence for OpenTTD."""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance

from openttd_contact_sheet_v1 import build as build_hover_sheet
from openttd_drag_effect_v1 import drag_box


def build(current_image, applied, proposal, runtime_dir, destination):
    current_image = Path(current_image)
    runtime_dir = Path(runtime_dir)
    destination = Path(destination)
    drags = [step for step in proposal.get('steps', []) if step.get('op') == 'pointer_drag']
    if not drags:
        return build_hover_sheet(current_image, applied, proposal, runtime_dir, destination)
    if len(drags) != 1:
        raise ValueError('at most one pointer_drag per planner turn')

    before_record = applied['fresh_observation']
    after_records = [record for record in applied['result']['reply']['records']
                     if record.get('event') == 'observation']
    if not after_records:
        raise ValueError('post-drag observation required')
    before_path = runtime_dir / Path(before_record['image']).name
    after_path = runtime_dir / Path(after_records[-1]['image']).name
    with Image.open(current_image) as opened:
        current = opened.convert('RGB')
    with Image.open(before_path) as opened:
        before = opened.convert('RGB')
    with Image.open(after_path) as opened:
        after = opened.convert('RGB')
    if current.size != before.size or before.size != after.size:
        raise ValueError('frame sizes differ')

    box = drag_box(drags[0], before.size)
    crops = [before.crop(box), after.crop(box)]
    difference = ImageEnhance.Contrast(ImageChops.difference(*crops)).enhance(4.0)
    scale = min(3, max(1, current.width // (3 * crops[0].width)))
    panels = [image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
              for image in (*crops, difference)]
    row_height = 30 + max(panel.height for panel in panels)
    sheet = Image.new('RGB', (current.width, current.height + row_height), 'black')
    sheet.paste(current, (0, 0))
    draw = ImageDraw.Draw(sheet)
    x = 0
    for label, panel in zip(('drag before', 'drag after', 'absolute RGB difference x4'), panels):
        sheet.paste(panel, (x, current.height + 30))
        draw.text((x + 6, current.height + 8), label, fill='white')
        x += panel.width
    sheet.save(destination)
    return destination
