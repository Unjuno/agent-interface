"""Inference helpers. The audit program deliberately reimplements these."""

from __future__ import annotations

import copy
from typing import Any

import torch


def run_full(model: Any, prefix_ids: torch.Tensor, suffix_ids: torch.Tensor) -> torch.Tensor:
    ids = torch.cat((prefix_ids, suffix_ids), dim=1)
    with torch.inference_mode():
        out = model(input_ids=ids, use_cache=False, return_dict=True)
    return out.logits[0, -1].float()


def run_cached(model: Any, prefix_cache: Any, prefix_len: int, suffix_ids: torch.Tensor) -> torch.Tensor:
    # Transformers' DynamicCache is mutable. Each independent suffix receives a
    # private copy so one question can never advance another question's state.
    cache = copy.deepcopy(prefix_cache)
    cache_position = torch.arange(
        prefix_len, prefix_len + suffix_ids.shape[1], dtype=torch.long, device=suffix_ids.device
    )
    attention_mask = torch.ones(
        (1, prefix_len + suffix_ids.shape[1]), dtype=torch.long, device=suffix_ids.device
    )
    with torch.inference_mode():
        out = model(
            input_ids=suffix_ids,
            past_key_values=cache,
            cache_position=cache_position,
            attention_mask=attention_mask,
            use_cache=True,
            return_dict=True,
        )
    return out.logits[0, -1].float()


def load_corpus(path: str) -> list[dict[str, Any]]:
    import json

    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    if len(rows) != 64 or any(len(row["suffixes"]) != 16 for row in rows):
        raise ValueError("frozen corpus dimensions differ")
    return rows
