from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Iterable

_V1 = Path(__file__).resolve().parent.parent / 'useful_control_interval_contract_v1'
if str(_V1) not in sys.path:
    sys.path.insert(0, str(_V1))

from interval_contract import EffectEvent, classify_effects


def valid_effect_id(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True)
class EffectRecord:
    effect_id: str
    event: EffectEvent


def classify_effect_records(
    records: Iterable[EffectRecord], known_actuation_ids: set[str]
) -> dict[str, int]:
    items = list(records)
    ids = []
    for record in items:
        if not valid_effect_id(record.effect_id):
            raise ValueError('invalid effect_id')
        ids.append(record.effect_id)
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate effect_id')
    return classify_effects(
        (record.event for record in items), known_actuation_ids
    )
