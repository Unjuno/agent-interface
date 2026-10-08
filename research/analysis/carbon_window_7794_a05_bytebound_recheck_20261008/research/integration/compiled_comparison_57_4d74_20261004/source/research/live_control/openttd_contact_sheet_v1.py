"""Preserve useful intermediate hover observations in one planner image."""
from pathlib import Path
from PIL import Image, ImageDraw


def build(current_image, applied, proposal, runtime_dir, destination):
    """Return current full frame plus toolbar strips captured after each dwell."""
    current_image = Path(current_image)
    runtime_dir = Path(runtime_dir)
    destination = Path(destination)
    dwell_steps = {
        index for index, step in enumerate(proposal.get('steps', []))
        if step.get('op') == 'dwell_observe'
    }
    observations = [
        record for record in applied['result']['reply']['records']
        if record.get('event') == 'observation' and record.get('step') in dwell_steps
    ]
    if not observations:
        return current_image

    with Image.open(current_image) as opened:
        base = opened.convert('RGB')
    strip_height = 125
    sheet = Image.new('RGB', (base.width, base.height + strip_height * len(observations)), 'black')
    sheet.paste(base, (0, 0))
    draw = ImageDraw.Draw(sheet)
    move_by_dwell = {}
    last_move = None
    for index, step in enumerate(proposal['steps']):
        if step.get('op') == 'pointer_move':
            last_move = (step['x'], step['y'])
        elif step.get('op') == 'dwell_observe':
            move_by_dwell[index] = last_move
    for row, observation in enumerate(observations):
        source = runtime_dir / Path(observation['image']).name
        with Image.open(source) as opened:
            frame = opened.convert('RGB')
        y = base.height + row * strip_height
        sheet.paste(frame.crop((0, 30, base.width, 145)), (0, y + 10))
        point = move_by_dwell.get(observation['step'])
        label = f"hover {row + 1}: {point}" if point else f"hover {row + 1}"
        draw.rectangle((0, y, 190, y + 18), fill='black')
        draw.text((5, y + 3), label, fill='white')
    sheet.save(destination)
    return destination
