"""Build bounded before/after evidence for pointer drags in retained OpenTTD runs."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def changed_pixels(left, right):
    difference = ImageChops.difference(left, right)
    return sum(pixel != (0, 0, 0) for pixel in difference.getdata())


def drag_box(step, size, padding=20):
    xs = [point['x'] for point in step['points']]
    ys = [point['y'] for point in step['points']]
    return (max(0, min(xs) - padding), max(0, min(ys) - padding),
            min(size[0], max(xs) + padding), min(size[1], max(ys) + padding))


def build(root, turn, destination):
    root = Path(root)
    typed = read(root / f'typed-{turn}.json')
    drags = [step for step in typed['steps'] if step.get('op') == 'pointer_drag']
    if len(drags) != 1:
        raise ValueError('exactly one pointer_drag required')
    applied = read(root / f'applied-{turn}.json')
    before_record = applied['fresh_observation']
    after_records = [record for record in applied['result']['reply']['records']
                     if record.get('event') == 'observation']
    if not after_records:
        raise ValueError('post-action observation required')
    after_record = after_records[-1]
    runtime = root / 'runtime'
    before_path = runtime / Path(before_record['image']).name
    after_path = runtime / Path(after_record['image']).name
    with Image.open(before_path) as opened:
        before = opened.convert('RGB')
    with Image.open(after_path) as opened:
        after = opened.convert('RGB')
    if before.size != after.size:
        raise ValueError('frame sizes differ')

    box = drag_box(drags[0], before.size)
    before_crop, after_crop = before.crop(box), after.crop(box)
    difference = ImageChops.difference(before_crop, after_crop)
    visible_difference = ImageEnhance.Contrast(difference).enhance(4.0)
    scale = 3
    panels = [image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
              for image in (before_crop, after_crop, visible_difference)]
    label_height = 30
    sheet = Image.new('RGB', (sum(panel.width for panel in panels), panels[0].height + label_height), 'black')
    draw = ImageDraw.Draw(sheet)
    x = 0
    for label, panel in zip(('before', 'after', 'absolute RGB difference x4'), panels):
        sheet.paste(panel, (x, label_height))
        draw.text((x + 6, 8), label, fill='white')
        x += panel.width
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)

    return {
        'turn': turn,
        'drag_points': drags[0]['points'],
        'before_sequence': before_record['sequence'],
        'after_sequence': after_record['sequence'],
        'before_image': before_path.relative_to(root).as_posix(),
        'after_image': after_path.relative_to(root).as_posix(),
        'crop_box': list(box),
        'crop_changed_pixels': changed_pixels(before_crop, after_crop),
        'crop_pixels': before_crop.width * before_crop.height,
        'full_frame_changed_pixels': changed_pixels(before, after),
        'full_frame_pixels': before.width * before.height,
        'sheet': destination.name,
        'sheet_sha256': sha(destination),
        'semantic_limit': 'pixel change alone does not establish construction success',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    parser.add_argument('turn', type=int)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.root, args.turn, args.destination), indent=2))


if __name__ == '__main__':
    main()
