"""Successor check for exact owner-bracket interval typing."""
from __future__ import annotations


class EvidenceError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def _is_exact_interval(value: object) -> bool:
    return (type(value) is list and len(value) == 2
            and all(type(endpoint) is int and endpoint >= 0 for endpoint in value)
            and value[0] <= value[1])


def owner_intervals(rows: list[dict]) -> dict[str, list[int]]:
    """Validate only the typed join under test; this grants no input authority."""
    _need(type(rows) is list and len(rows) == 2, "one down/up pair is required")
    result: dict[str, list[int]] = {}
    for row, edge_name, interval_name in (
            (rows[0], "down", "physical_down_interval"),
            (rows[1], "up", "physical_up_interval")):
        measurement = row.get("physical_key_measurement")
        _need(type(measurement) is dict, "measurement object is required")
        edge, bracket = measurement.get("adapter_edge"), measurement.get("bracket")
        _need(type(edge) is dict and type(bracket) is dict,
              "edge and bracket objects are required")
        edge_interval = edge.get("interval")
        bracket_interval = bracket.get(interval_name)
        _need(_is_exact_interval(edge_interval), "edge interval is not exact")
        _need(_is_exact_interval(bracket_interval), "owner interval is not exact")
        _need(edge.get("edge") == edge_name, "edge direction mismatch")
        _need(bracket_interval == edge_interval,
              "owner interval disagrees with edge interval")
        result[edge_name] = list(bracket_interval)
    return result
