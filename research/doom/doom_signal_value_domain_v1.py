"""Validated numeric domains for the exact three-slot MAP01 HUD signals."""
from types import MappingProxyType

SIGNAL_VALUE_RANGES = MappingProxyType({
    "health": (1, 200),
    "ammo": (0, 999),
})


def signal_value_in_domain(signal_id, value):
    bounds = SIGNAL_VALUE_RANGES.get(signal_id)
    return (bounds is not None and type(value) is int and
            bounds[0] <= value <= bounds[1])
