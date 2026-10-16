"""Saved-pixel diagnosis only; never emits input or grants controller authority."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np
from PIL import Image, __version__ as pillow_version


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wad', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    here = Path(__file__).resolve().parent
    freeze = json.loads((here / 'FREEZE.json').read_text())
    for relative, expected in freeze['repo_sha256'].items():
        if digest((root / relative).read_bytes()) != expected:
            raise ValueError('source/input hash mismatch: ' + relative)
    if digest(args.wad.read_bytes()) != freeze['wad_sha256']:
        raise ValueError('WAD hash mismatch')
    # Exclusive output directory makes accidental replay fail before reading pixels.
    args.output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    sys.path.insert(0, str(root / 'research/doom'))
    from doom_hud_signal_v1 import _wad_lumps, _render_patch
    from doom_hud_signal_v3 import DoomStatusNumberReader
    archive = root / freeze['archive']
    observations = [json.loads(line) for line in
                    (archive / 'guarded/run/episode/runtime/events.jsonl').read_text().splitlines()]
    selected = {seq: [row for row in observations if row.get('event') == 'observation'
                      and row.get('sequence') == seq] for seq in freeze['sequences']}
    if any(len(rows) != 1 for rows in selected.values()):
        raise ValueError('not exactly one retained observation per selected sequence')
    lumps = _wad_lumps(args.wad, freeze['wad_sha256'])
    playpal = lumps['PLAYPAL']
    if not playpal or len(playpal) % 768:
        raise ValueError('incomplete PLAYPAL palette')
    palettes = np.frombuffer(playpal, dtype=np.uint8).reshape(-1, 256, 3)
    templates = []
    for palette in palettes:
        group = []
        for digit in range(10):
            patch = Image.fromarray(_render_patch(lumps[f'STTNUM{digit}'], palette))
            resized = np.asarray(patch.resize((26, 38), Image.Resampling.NEAREST))
            group.append((resized[:, :, :3], resized[:, :, 3] > 0))
        templates.append(group)
    rows = []
    for seq in freeze['sequences']:
        obs = dict(selected[seq][0])
        image_path = archive / 'guarded/run/episode/runtime' / f'{seq:03}.png'
        obs['image'] = str(image_path)
        with Image.open(image_path) as opened:
            frame = opened.convert('RGB')
        rgb_hash = digest(frame.tobytes())
        if rgb_hash != obs['frame_rgb_sha256']:
            raise ValueError('retained PNG does not join observation frame RGB hash')
        for signal in ('health', 'ammo'):
            reader = DoomStatusNumberReader(args.wad, signal_id=signal)
            baseline = reader.read_frame(obs, frame)
            variants = []
            for index, template_group in enumerate(templates):
                reader.templates = template_group
                outcome = reader.read_frame(obs, frame)
                variants.append({'palette': index, 'outcome': outcome})
            if variants[0]['outcome'] != baseline:
                raise ValueError('palette-zero reconstruction differs from unchanged reader')
            rows.append({'sequence': seq, 'signal': signal, 'frame_rgb_sha256': rgb_hash,
                         'baseline': baseline, 'palette_variants': variants})
    result = {'kind': 'saved_pixel_diagnostic_not_controller_authority',
              'started_at': started, 'finished_at': datetime.now(timezone.utc).isoformat(),
              'python': platform.python_version(), 'platform': platform.platform(),
              'pillow': pillow_version, 'numpy': np.__version__,
              'freeze_sha256': digest((here / 'FREEZE.json').read_bytes()),
              'playpal_sha256': digest(playpal), 'palette_count': len(palettes),
              'rows': rows}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    for row in rows:
        accepted = [(v['palette'], v['outcome']['value']) for v in row['palette_variants']
                    if v['outcome']['status'] == 'observed']
        print(json.dumps({'sequence': row['sequence'], 'signal': row['signal'],
                          'baseline': row['baseline']['value'], 'accepted_palettes': accepted}))


if __name__ == '__main__':
    main()
