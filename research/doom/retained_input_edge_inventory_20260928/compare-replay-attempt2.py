import json
from pathlib import Path
root=Path(__file__).resolve().parent
recorded=json.loads((root/'result-attempt2.json').read_text(encoding='utf-8-sig'))
replayed=json.loads((root/'branch-replay-attempt2.json').read_text(encoding='utf-8-sig'))
assert recorded == replayed, {'recorded_files':[x['file'] for x in recorded['runs']], 'replayed_files':[x['file'] for x in replayed['runs']]}
