"""Fully specified synthetic RGB inputs, not captured/held-out application data."""
import numpy as np
from codec import Frame

SIZES = [(129, 97), (320, 240), (641, 481)]
SCENES = ['UNCHANGED', 'LOCAL', 'SCATTER', 'DENSE_SOLID', 'DENSE_PATTERN', 'DENSE_TILE_REPEAT']


def frames(width, height, scene):
    y, x, c = np.indices((height, width, 3), dtype=np.int32)
    old = ((3*x + 5*y + 71*c) % 256).astype(np.uint8)
    new = old.copy()
    if scene == 'UNCHANGED':
        pass
    elif scene == 'LOCAL':
        new[-8:, -8:] ^= 255
    elif scene == 'SCATTER':
        for j in range(0, height, 64):
            for i in range(0, width, 64):
                if ((j//64) + (i//64)) % 2 == 0:
                    new[j, i] ^= 255
    elif scene == 'DENSE_SOLID':
        old[:] = 0
        new[:] = 17
    elif scene == 'DENSE_PATTERN':
        new ^= 55
    elif scene == 'DENSE_TILE_REPEAT':
        old[:] = 0
        new = (((x % 16)*17 + (y % 16)*29 + c*67) % 256).astype(np.uint8)
    else:
        raise ValueError('unknown fixture')
    return Frame(width, height, 'RGB', old.tobytes()), Frame(width, height, 'RGB', new.tobytes())
