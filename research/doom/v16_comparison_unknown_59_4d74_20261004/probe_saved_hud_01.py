import json
from pathlib import Path
from PIL import Image
from doom_hud_signal_v3 import DoomStatusNumberReader

rows = [json.loads(line) for line in Path('/study/comparison-guarded-01/episode/runtime/events.jsonl').read_bytes().splitlines()]
results = []
for row in rows:
    if row.get('event') != 'observation' or row.get('sequence') not in (31, 35):
        continue
    observation = dict(row)
    observation['image'] = '/study/comparison-guarded-01/episode/runtime/' + Path(row['image']).name
    for signal in ('health', 'ammo'):
        reader = DoomStatusNumberReader('/study/fixture-input/freedoom2.wad', signal_id=signal)
        with Image.open(observation['image']) as frame:
            memory = reader.read_frame(observation, frame)
        results.append({'sequence': row['sequence'], 'signal': signal, 'file': reader.read(observation), 'memory': memory})
Path('/out/result.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results))
