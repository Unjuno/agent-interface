"""Opt-in palette-aware HUD reader; no controller imports this version yet."""
from copy import copy

import numpy as np
from PIL import Image

from doom_hud_signal_v1 import _wad_lumps, _render_patch
from doom_hud_signal_v3 import DoomStatusNumberReader as Previous


class DoomStatusNumberReader(Previous):
    def __init__(self, wad_path, signal_id='health', local_anchor=None, **kwargs):
        super().__init__(wad_path, signal_id=signal_id, local_anchor=local_anchor, **kwargs)
        lumps = _wad_lumps(wad_path, self.wad_sha256)
        data = lumps['PLAYPAL']
        if len(data) != 14 * 768:
            raise ValueError('frozen fourteen-palette WAD required')
        self.palette_templates = []
        self.blank_templates = []
        self.blank_neighborhoods = []
        self.background_colors = []
        for palette in np.frombuffer(data, dtype=np.uint8).reshape(14, 256, 3):
            group = []
            for digit in range(10):
                patch = Image.fromarray(_render_patch(lumps[f'STTNUM{digit}'], palette))
                resized = np.asarray(patch.resize(self.glyph_size, Image.Resampling.NEAREST))
                group.append((resized[:, :, :3], resized[:, :, 3] > 0))
            self.palette_templates.append(tuple(group))
            # Canonical Doom HUD: 320x32 status bar at y=168 in a 320x200 frame.
            bar = Image.fromarray(_render_patch(lumps['STBAR'], palette))
            if bar.size != (320, 32):
                raise ValueError('frozen status-bar geometry required')
            canvas = Image.new('RGBA', (320, 200))
            canvas.paste(bar, (0, 168))
            background = canvas.resize(self.client_size, Image.Resampling.NEAREST).convert('RGB')
            x, y = self.local_anchor
            self.blank_templates.append(tuple(np.asarray(background.crop(
                (x + 26 * slot, y, x + 26 * (slot + 1), y + 38))) for slot in range(3)))
            # One output-pixel allowance for nearest-scale integer rounding.
            # Colors must remain locally plausible, not merely occur somewhere
            # else in the status bar (a partial glyph can share those colors).
            self.blank_neighborhoods.append(tuple(np.stack([
                np.asarray(background.crop((x + 26 * slot + dx, y + dy,
                                             x + 26 * (slot + 1) + dx, y + 38 + dy)))
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)]) for slot in range(3)))
            self.background_colors.append(np.unique(self._rgb_codes(np.asarray(bar)[:, :, :3])))
        self.palette_templates = tuple(self.palette_templates)
        self.blank_templates = tuple(self.blank_templates)
        self.blank_neighborhoods = tuple(self.blank_neighborhoods)
        self.background_colors = tuple(self.background_colors)

    @staticmethod
    def _rgb_codes(rgb):
        values = rgb.astype(np.uint32)
        return (values[:, :, 0] << 16) | (values[:, :, 1] << 8) | values[:, :, 2]

    def read_frame(self, observation, frame):
        candidates = []
        variants = []
        baseline = None
        for index, templates in enumerate(self.palette_templates):
            variant = copy(self)
            variant.templates = templates
            result = Previous.read_frame(variant, observation, frame)
            if baseline is None:
                baseline = result
            variants.append(result)
            if result['status'] == 'observed':
                candidates.append((index, result))
        if not candidates:
            return baseline
        # Ambiguous glyph evidence in any palette cannot be discarded in favor of
        # another interpretation just because that interpretation is complete.
        if any(result.get('reason') == 'ambiguous_digit' for result in variants):
            return self._unknown('ambiguous_palette_digit', observation.get('sequence'),
                                 observation.get('capture_ns'), observation.get('pointer_binding'))
        geometry = observation['pointer_binding']['geometry']
        left = geometry[0] + self.local_anchor[0]
        top = geometry[1] + self.local_anchor[1]
        number = np.asarray(frame.convert('RGB').crop((left, top, left + 78, top + 38)))
        validated = []
        for palette, result in candidates:
            blank_evidence = []
            for slot in result['slots']:
                if slot['digit'] is not None:
                    break
                index = slot['slot']
                pixels = number[:, index * 26:(index + 1) * 26]
                background_score = float(np.all(
                    pixels == self.blank_templates[palette][index], axis=2).mean())
                colors_valid = bool(np.isin(self._rgb_codes(pixels),
                                           self.background_colors[palette]).all())
                local_colors_valid = bool(np.all(np.any(np.all(
                    self.blank_neighborhoods[palette][index] == pixels, axis=3), axis=0)))
                # This is a veto only, never a number assembled across palettes.
                foreign_score = max(v.get('slots', v.get('detail', {}).get('slots', []))[index]['best_score']
                                    for v in variants)
                if (background_score < self.minimum_score or not colors_valid or not local_colors_valid or
                        foreign_score >= self.minimum_score):
                    break
                blank_evidence.append({'slot': index, 'background_score': background_score,
                                       'background_colors_only': True,
                                       'local_background_colors_only': True,
                                       'maximum_glyph_score_any_palette': foreign_score})
            else:
                # All three slots were blank; Previous never accepts this case.
                continue
            first_digit = next(s['slot'] for s in result['slots'] if s['digit'] is not None)
            if len(blank_evidence) == first_digit:
                result['leading_blank_evidence'] = blank_evidence
                validated.append((palette, result))
        candidates = validated
        if not candidates:
            return self._unknown('unproven_leading_blank', observation.get('sequence'),
                                 observation.get('capture_ns'), observation.get('pointer_binding'))
        if len({result['value'] for _, result in candidates}) != 1:
            return self._unknown('conflicting_palette_values', observation.get('sequence'),
                                 observation.get('capture_ns'), observation.get('pointer_binding'))
        _, result = candidates[0]
        result['palette_indices'] = [index for index, _ in candidates]
        result['evidence'] = 'hash-bound WAD palette-consistent glyphs with checked leading background'
        return result

    def read(self, observation):
        metadata = Previous.read_frame(self, observation, None)
        if metadata.get('reason') != 'frame_unavailable':
            return metadata
        try:
            with Image.open(self.image_resolver(observation['image'])) as opened:
                frame = opened.convert('RGB')
        except (KeyError, OSError, ValueError):
            return self._unknown('image_unavailable', observation.get('sequence'),
                                 observation.get('capture_ns'), observation.get('pointer_binding'))
        return self.read_frame(observation, frame)
