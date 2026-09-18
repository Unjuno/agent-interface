from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class Frame:
    blocks: Tuple[int, ...]
    overrides: Tuple[Tuple[int, int], ...] = ()

    def __post_init__(self):
        if len(self.blocks) != 64:
            raise ValueError('bad_block_count')
        if any((not isinstance(v, int)) or v < 0 or v > 255 for v in self.blocks):
            raise ValueError('bad_block_value')
        seen=set()
        for idx, val in self.overrides:
            if not isinstance(idx, int) or idx < 0 or idx >= 4096:
                raise ValueError('bad_pixel_index')
            if not isinstance(val, int) or val < 0 or val > 255:
                raise ValueError('bad_pixel_value')
            if idx in seen:
                raise ValueError('duplicate_override')
            seen.add(idx)

    def canonical(self):
        return self.blocks, tuple(sorted(self.overrides))

def block_sums(frame: Frame) -> list[int]:
    sums=[v*64 for v in frame.blocks]
    for idx,new in frame.overrides:
        b=idx//64
        sums[b]+=new-frame.blocks[b]
    return sums

def ahash64(frame: Frame) -> int:
    sums=block_sums(frame)
    total=sum(sums)
    h=0
    for b,s in enumerate(sums):
        if s*64 >= total:
            h |= 1 << b
    return h

def exact_equal(a: Frame, b: Frame) -> bool:
    return a.canonical() == b.canonical()

def global_ahash_only(a: Frame, b: Frame) -> dict:
    equal_hash = ahash64(a) == ahash64(b)
    return {'suppress': equal_hash, 'hash_equal': equal_hash, 'exact_fallback': False}

def ahash_plus_exact_fallback(a: Frame, b: Frame) -> dict:
    equal_hash = ahash64(a) == ahash64(b)
    if not equal_hash:
        return {'suppress': False, 'hash_equal': False, 'exact_fallback': False}
    same = exact_equal(a,b)
    return {'suppress': same, 'hash_equal': True, 'exact_fallback': True}
