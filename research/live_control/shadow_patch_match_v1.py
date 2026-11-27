"""Bounded, observational-only RGB patch search for research experiments.

A numerical match is not target identity or permission to dispatch input.
Caller must establish freshness, binding, semantic identity and custody separately.
"""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def search(source, checked, origin):
    """Score a fixed 16x16 template over a clipped, two-pixel search grid.

    Inputs must be equal-size uint8 RGB arrays and a center (x, y), with the
    entire source template in bounds. No control authority is returned.
    """
    if (not isinstance(source, np.ndarray) or not isinstance(checked, np.ndarray)
            or source.dtype != np.uint8 or checked.dtype != np.uint8
            or source.ndim != 3 or source.shape != checked.shape
            or source.shape[2] != 3 or source.shape[0] * source.shape[1] > 4_000_000
            or type(origin) is not tuple or len(origin) != 2
            or any(type(v) is not int for v in origin)):
        raise ValueError('equal bounded uint8 RGB arrays and integer center required')
    height, width = source.shape[:2]
    x, y = origin
    if not (8 <= x <= width - 8 and 8 <= y <= height - 8):
        raise ValueError('source template must fit within the image')
    dxs = [d for d in range(-80, 81, 2) if 8 <= x+d <= width-8]
    dys = [d for d in range(-60, 61, 2) if 8 <= y+d <= height-8]
    template = source[y-8:y+8, x-8:x+8].astype(np.int16).transpose(2, 0, 1)
    region = checked[y+dys[0]-8:y+dys[-1]+8, x+dxs[0]-8:x+dxs[-1]+8]
    windows = sliding_window_view(region, (16, 16), axis=(0, 1))[::2, ::2]
    sums = np.abs(windows.astype(np.int16) - template).sum(axis=(2, 3, 4), dtype=np.int64)
    rows = sorted((int(sums[i, j]), dx, dy) for i, dy in enumerate(dys) for j, dx in enumerate(dxs))
    best = rows[0]
    runner = next((q for q in rows[1:] if abs(q[1]-best[1]) > 16 or abs(q[2]-best[2]) > 16), None)
    return {'candidate': (x+best[1], y+best[2]), 'best_sum': best[0],
            'runner_sum': None if runner is None else runner[0],
            'candidate_count': len(rows), 'authority_granted': False,
            'requires_revalidation': True}
