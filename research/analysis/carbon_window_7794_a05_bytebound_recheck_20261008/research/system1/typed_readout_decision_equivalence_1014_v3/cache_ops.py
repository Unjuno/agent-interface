"""Generation-bound isolated prefix caches for Issue #4652."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import torch


@dataclass(frozen=True)
class PrefixCache:
    value: Any
    bundle_id: str
    generation: int
    digest: str
    length: int

    def clone(self, *, bundle_id: str, generation: int, digest: str) -> Any:
        if (bundle_id, generation, digest) != (self.bundle_id, self.generation, self.digest):
            raise ValueError("stale_or_foreign_prefix_cache")
        return copy.deepcopy(self.value)


def full_scores(model: Any, prefix: torch.Tensor, suffix: torch.Tensor) -> torch.Tensor:
    ids = torch.cat((prefix, suffix), dim=1)
    with torch.inference_mode():
        out = model(input_ids=ids, use_cache=False, return_dict=True)
    return out.logits[0, -1].float()


def cached_scores(
    model: Any, cache: PrefixCache, *, bundle_id: str, generation: int,
    digest: str, suffix: torch.Tensor,
) -> torch.Tensor:
    past = cache.clone(bundle_id=bundle_id, generation=generation, digest=digest)
    position = torch.arange(cache.length, cache.length + suffix.shape[1], device=suffix.device)
    mask = torch.ones((1, cache.length + suffix.shape[1]), dtype=torch.long, device=suffix.device)
    with torch.inference_mode():
        out = model(input_ids=suffix, past_key_values=past, cache_position=position,
                    attention_mask=mask, use_cache=True, return_dict=True)
    return out.logits[0, -1].float()
