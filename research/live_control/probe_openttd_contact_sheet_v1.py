"""Small deterministic contact-sheet construction probe."""
import json
import tempfile
from pathlib import Path
from PIL import Image
from openttd_contact_sheet_v1 import build


with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    current = root / 'current.png'
    hovered = root / 'hovered.png'
    Image.new('RGB', (1280, 800), '#123456').save(current)
    Image.new('RGB', (1280, 800), '#654321').save(hovered)
    applied = {'result': {'reply': {'records': [
        {'event': 'observation', 'step': 1, 'image': str(hovered)}
    ]}}}
    proposal = {'steps': [
        {'op': 'pointer_move', 'x': 900, 'y': 51},
        {'op': 'dwell_observe', 'delay_ms': 800},
    ]}
    out = root / 'sheet.png'
    result = build(current, applied, proposal, root, out)
    with Image.open(result) as image:
        assert image.size == (1280, 925)
        assert image.getpixel((1000, 850)) == (101, 67, 33)
    print(json.dumps({'success': True, 'size': [1280, 925]}))
