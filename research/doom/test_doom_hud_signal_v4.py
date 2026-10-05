"""Finite repair regressions; generated pixels are not live accuracy evidence."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from doom_hud_signal_v1 import _wad_lumps, _render_patch, FREEDOOM2_SHA256
from doom_hud_signal_v3 import DoomStatusNumberReader as V3
from doom_hud_signal_v4 import DoomStatusNumberReader

WAD = Path(os.environ.get('DOOM_TEST_WAD', HERE.parents[1] / '_vizdoom/vizdoom/freedoom2.wad'))
ARCHIVE = HERE / 'v16_comparison_unknown_59_4d74_20261004/guarded/run/episode/runtime'


class PaletteReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readers = {s: DoomStatusNumberReader(WAD, signal_id=s) for s in ('health', 'ammo')}
        cls.lumps = _wad_lumps(WAD, FREEDOOM2_SHA256)
        cls.palettes = np.frombuffer(cls.lumps['PLAYPAL'], dtype=np.uint8).reshape(14, 256, 3)

    def observation(self):
        return {'sequence': 1, 'capture_ns': 2, 'pointer_binding': {
            'focus': 1, 'surface': 1, 'geometry': [0, 0, 640, 480]}}

    def background(self, palette):
        patch = Image.fromarray(_render_patch(self.lumps['STBAR'], self.palettes[palette]))
        frame = Image.new('RGBA', (320, 200))
        frame.paste(patch, (0, 168))
        return frame.resize((640, 480), Image.Resampling.NEAREST).convert('RGB')

    def place_digit(self, frame, signal, slot, digit, palette):
        reader = self.readers[signal]
        rgb, mask = self.fixture_glyph(digit, palette)
        x, y = reader.local_anchor
        frame.paste(Image.fromarray(rgb), (x + 26 * slot, y), Image.fromarray(mask.astype('uint8') * 255))

    def fixture_glyph(self, digit, palette):
        # Render fixture pixels from the source WAD, not the V4 candidate bank.
        patch = Image.fromarray(_render_patch(self.lumps[f'STTNUM{digit}'], self.palettes[palette]))
        rgba = np.asarray(patch.resize((26, 38), Image.Resampling.NEAREST))
        return rgba[:, :, :3], rgba[:, :, 3] > 0

    def rendered(self, signal, value, palette):
        frame = self.background(palette)
        digits = str(value)
        for slot, digit in enumerate(digits, 3 - len(digits)):
            self.place_digit(frame, signal, slot, int(digit), palette)
        return frame

    def test_generated_numbers_all_palettes(self):
        for signal, reader in self.readers.items():
            for palette in range(14):
                for value in (0, 7, 47, 97, 100, 197, 999):
                    with self.subTest(signal=signal, palette=palette, value=value):
                        result = reader.read_frame(self.observation(), self.rendered(signal, value, palette))
                        self.assertEqual((result['status'], result['value']), ('observed', value))
                        self.assertIn(palette, result['palette_indices'])

    def test_saved_original_unknown_and_normal_frames(self):
        events = [json.loads(line) for line in (ARCHIVE / 'events.jsonl').read_text().splitlines()]
        for seq, values in ((31, {'health': 97, 'ammo': 47}), (35, {'health': 100, 'ammo': 47})):
            obs = next(row for row in events if row.get('event') == 'observation' and row['sequence'] == seq)
            with Image.open(ARCHIVE / f'{seq:03}.png') as frame:
                for signal, value in values.items():
                    with self.subTest(seq=seq, signal=signal):
                        self.assertEqual(self.readers[signal].read_frame(obs, frame)['value'], value)
                        old = V3(WAD, signal_id=signal).read_frame(obs, frame)
                        self.assertEqual(old['value'], value if seq == 31 else None)

    def test_foreign_palette_leading_digit_does_not_become_blank(self):
        frame = self.rendered('health', 100, 9)
        frame.paste(self.background(9).crop((102, 411, 128, 449)), (102, 411))
        self.place_digit(frame, 'health', 0, 1, 0)
        result = self.readers['health'].read_frame(self.observation(), frame)
        self.assertEqual(result['status'], 'unknown', result)

    def test_partial_leading_digit_does_not_become_blank(self):
        frame = self.rendered('health', 147, 9)
        # Occlude the left 20/26 columns with their true background; visible ink remains.
        background = self.background(9)
        frame.paste(background.crop((102, 411, 122, 449)), (102, 411))
        result = self.readers['health'].read_frame(self.observation(), frame)
        self.assertEqual(result['status'], 'unknown', result)

    def test_foreground_pixel_in_blank_prefix_is_not_proven_blank(self):
        frame = self.rendered('ammo', 47, 9)
        rgb, mask = self.fixture_glyph(1, 9)
        colored = np.argwhere(mask & (rgb[:, :, 0].astype(int) > rgb[:, :, 1].astype(int) + 10))
        y, x = colored[0]
        frame.putpixel((10 + int(x), 411 + int(y)), tuple(int(v) for v in rgb[y, x]))
        result = self.readers['ammo'].read_frame(self.observation(), frame)
        self.assertEqual(result['status'], 'unknown', result)

    def test_blank_flat_and_noise_frames_abstain(self):
        frames = [self.background(0), self.background(9)]
        frames += [Image.new('RGB', (640, 480), color) for color in ('black', 'white', 'gray', 'red')]
        frames.append(Image.fromarray(np.random.default_rng(59).integers(0, 256, (480, 640, 3), dtype=np.uint8)))
        for index, frame in enumerate(frames):
            for signal, reader in self.readers.items():
                with self.subTest(index=index, signal=signal):
                    self.assertEqual(reader.read_frame(self.observation(), frame)['status'], 'unknown')

    def test_png_and_memory_agree_and_binding_is_copied(self):
        frame = self.rendered('ammo', 47, 9)
        obs = self.observation()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'frame.png'; frame.save(path); obs['image'] = str(path)
            direct = self.readers['ammo'].read_frame(obs, frame)
            self.assertEqual(self.readers['ammo'].read(obs), direct)
        obs['pointer_binding']['geometry'][0] = 2
        self.assertEqual(direct['binding']['geometry'][0], 0)

    def test_metadata_geometry_and_missing_image_fail_closed(self):
        reader = self.readers['health']; frame = self.rendered('health', 100, 9)
        for key, value in (('sequence', True), ('capture_ns', 0), ('pointer_binding', None)):
            obs = self.observation(); obs[key] = value
            self.assertEqual(reader.read_frame(obs, frame)['status'], 'unknown')
        obs = self.observation(); obs['pointer_binding']['geometry'][2] = 320
        self.assertEqual(reader.read_frame(obs, frame)['status'], 'unknown')
        self.assertEqual(reader.read_frame(self.observation(), None)['status'], 'unknown')
        self.assertEqual(reader.read(dict(self.observation(), image='missing.png'))['status'], 'unknown')

    def test_positional_signal_and_metadata_before_file_access(self):
        reader = DoomStatusNumberReader(WAD, 'ammo')
        self.assertEqual(reader.signal_id, 'ammo')
        reader.image_resolver = lambda path: self.fail('invalid metadata must not resolve an image')
        obs = self.observation(); obs['sequence'] = True; obs['image'] = 'unused.png'
        self.assertEqual(reader.read(obs)['reason'], 'invalid_observation_metadata')

    def test_disagreeing_complete_palette_values_abstain(self):
        # Collision fixture: one palette interprets the same complete glyphs as
        # 100, another as 188. Values must never be resolved by palette ordering.
        from copy import copy
        reader = copy(self.readers['health'])
        original = reader.palette_templates[0]
        swapped = list(original); swapped[0], swapped[8] = swapped[8], swapped[0]
        reader.palette_templates = (original, tuple(swapped))
        result = reader.read_frame(self.observation(), self.rendered('health', 100, 0))
        self.assertEqual((result['status'], result['reason']), ('unknown', 'conflicting_palette_values'))

    def test_typed_observation_and_admission_preserve_unknown(self):
        sys.path.insert(0, str(HERE.parent / 'live_control'))
        from doom_typed_observation_v1 import extract_typed_observation, build_action_snapshot
        from action_validity_admission_v1 import CONTRACT_FORMAT, action_fingerprint, evaluate_action_validity
        obs = dict(self.observation(), id='palette-regression', step=1)
        action = {'kind': 'synthetic-no-executor-call'}
        contract = {'format': CONTRACT_FORMAT, 'action_fingerprint': action_fingerprint(action),
                    'source': {'sequence': 0, 'capture_ns': 1,
                               'binding': deepcopy(obs['pointer_binding']),
                               'signals': {'health': {'status': 'observed', 'value': 100},
                                           'ammo': {'status': 'observed', 'value': 47}}},
                    'max_current_age_ms': 100,
                    'predicates': [{'signal_id': 'health', 'operator': 'minimum', 'value': 1},
                                   {'signal_id': 'ammo', 'operator': 'minimum', 'value': 1}]}
        for corrupted in (False, True):
            with self.subTest(corrupted=corrupted):
                frame = self.rendered('health', 100, 9)
                for slot, digit in ((1, 4), (2, 7)):
                    self.place_digit(frame, 'ammo', slot, digit, 9)
                if corrupted:
                    frame.paste(self.background(9).crop((102, 411, 128, 449)), (102, 411))
                    self.place_digit(frame, 'health', 0, 1, 0)
                ticks = iter((3, 4))
                event = extract_typed_observation(frame, obs, self.readers, clock=lambda: next(ticks))
                snapshot = build_action_snapshot(event, contract)
                verdict = evaluate_action_validity(action, contract, snapshot, 5)
                self.assertEqual(verdict['status'], 'REJECTED_SIGNAL_UNKNOWN' if corrupted else 'VALID_CURRENT')
                self.assertIs(event['grants_input_authority'], False)
                self.assertIs(verdict['grants_input_authority'], False)
                self.assertEqual(verdict['action_may_proceed_to_executor_admission'], not corrupted)


if __name__ == '__main__':
    unittest.main()
