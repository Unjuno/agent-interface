"""Generation-bound immutable prefix-cache handles for Issue #4639."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import torch


@dataclass(frozen=True)
class CacheHandle:
    cache: Any
    bundle_id: str
    generation: int
    prefix_sha256: str
    prefix_length: int

    def private_copy(self, *, bundle_id: str, generation: int, prefix_sha256: str) -> Any:
        if (bundle_id, generation, prefix_sha256) != (
            self.bundle_id, self.generation, self.prefix_sha256
        ):
            raise ValueError("stale_or_foreign_prefix_cache")
        return copy.deepcopy(self.cache)


def full_logits(model: Any, prefix_ids: torch.Tensor, suffix_ids: torch.Tensor) -> torch.Tensor:
    input_ids = torch.cat((prefix_ids, suffix_ids), dim=1)
    with torch.inference_mode():
        output = model(input_ids=input_ids, use_cache=False, return_dict=True)
    return output.logits[0, -1].float()


def cached_logits(
    model: Any,
    handle: CacheHandle,
    *,
    bundle_id: str,
    generation: int,
    prefix_sha256: str,
    suffix_ids: torch.Tensor,
) -> torch.Tensor:
    cache = handle.private_copy(
        bundle_id=bundle_id, generation=generation, prefix_sha256=prefix_sha256
    )
    position = torch.arange(
        handle.prefix_length,
        handle.prefix_length + suffix_ids.shape[1],
        device=suffix_ids.device,
    )
    mask = torch.ones(
        (1, handle.prefix_length + suffix_ids.shape[1]),
        dtype=torch.long,
        device=suffix_ids.device,
    )
    with torch.inference_mode():
        output = model(input_ids=suffix_ids, past_key_values=cache,
                       cache_position=position, attention_mask=mask,
                       use_cache=True, return_dict=True)
    return output.logits[0, -1].float()
