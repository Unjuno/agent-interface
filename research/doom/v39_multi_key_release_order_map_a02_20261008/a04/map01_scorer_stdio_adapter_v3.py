"""Strict adapter for distinct per-key admission and release-measurement rows."""
from __future__ import annotations

from dataclasses import dataclass

from map01_scorer_stdio_adapter_v1 import MainThreadScorerStdin as _LegacyScorerStdin


class MeasuredReleaseError(ValueError):
    """The raw down/up rows cannot establish a usable post-release boundary."""


@dataclass(frozen=True)
class MeasuredReleaseBoundary:
    schema: str
    program_id: str
    step: int
    key: str
    owner_id: str
    intent_token: str
    actuation_id: str
    release_after_ns: int
    source_event_types: tuple[str, str]


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise MeasuredReleaseError(reason)


def _exact_ns(value: object) -> bool:
    return type(value) is int and value >= 0


def _measure(row: dict, edge_name: str, classification: str,
             identity_status: str) -> tuple[dict, dict, dict, list[int]]:
    measurement = row.get("physical_key_measurement")
    _need(type(measurement) is dict, "physical key measurement is missing")
    edge = measurement.get("adapter_edge")
    bracket = measurement.get("bracket")
    _need(type(edge) is dict and type(bracket) is dict,
          "adapter edge and source bracket are required")
    interval = edge.get("interval")
    _need(type(interval) is list and len(interval) == 2
          and all(_exact_ns(value) for value in interval),
          "edge interval must contain two exact monotonic timestamps")
    _need(interval[0] <= interval[1], "edge interval is reversed")
    _need(measurement.get("grants_input_authority") is False
          and edge.get("grants_input_authority") is False,
          "measurement may not grant input authority")
    _need(measurement.get("application_consumption_observed") is False,
          "application consumption must remain unobserved")
    _need(row.get("grants_input_authority", False) is False,
          "event may not grant input authority")
    _need(measurement.get("edge") == edge_name
          and edge.get("edge") == edge_name,
          f"expected a physical {edge_name} edge")
    _need(measurement.get("classification") == classification
          and edge.get("status") == classification,
          f"physical {edge_name} edge is not confirmed")
    _need(measurement.get("identity_status") == identity_status,
          f"physical {edge_name} actuation identity is not {identity_status.lower()}")
    _need(type(measurement.get("actuation_id")) is str
          and bool(measurement["actuation_id"]),
          "actuation identity is required")
    identity = (row.get("owner_id"), row.get("intent_token"), row.get("key"))
    _need(all(type(value) is str and bool(value.strip()) for value in identity),
          "owner, intent and key identities are required")
    for layer in (edge, bracket):
        _need((layer.get("owner_id"), layer.get("intent_token"), layer.get("key")) == identity,
              "nested physical edge identity differs from the event")
    source_interval = bracket.get("physical_down_interval" if edge_name == "down"
                                  else "physical_up_interval")
    _need(bracket.get("status") == classification and source_interval == interval,
          "source bracket differs from the physical edge interval")
    return measurement, edge, bracket, interval


def validate_measured_release_pair(down: dict, release: dict, *,
                                   backend_held_after: list[str]) -> MeasuredReleaseBoundary:
    """Join exact raw events and return the first safe post-up sample boundary.

    The raw `input_admission` and `input_release_measurement` events remain
    distinct. This projection neither renames them nor claims game consumption.
    """
    _need(type(down) is dict and type(release) is dict,
          "down and release events must be objects")
    _need(down.get("event") == "input_admission",
          "down row must remain input_admission")
    _need(release.get("event") == "input_release_measurement",
          "release row must remain input_release_measurement")
    _need(type(backend_held_after) is list and backend_held_after == [],
          "backend must report no remaining held keys")
    down_identity = (down.get("id"), down.get("step"), down.get("owner_id"),
                     down.get("intent_token"), down.get("key"))
    release_identity = (release.get("id"), release.get("step"), release.get("owner_id"),
                        release.get("intent_token"), release.get("key"))
    _need(down_identity == release_identity,
          "program/step/owner/intent/key identities differ")
    _need(type(down_identity[0]) is str and bool(down_identity[0].strip()),
          "program identifier is required")
    _need(type(down_identity[1]) is int and down_identity[1] >= 0,
          "step must be an exact nonnegative integer")
    _need(all(type(value) is str and bool(value.strip()) for value in down_identity[2:]),
          "owner, intent and key identities are required")

    down_measurement, down_edge, down_bracket, down_interval = _measure(
        down, "down", "CONFIRMED_PHYSICAL_DOWN", "MINTED")
    up_measurement, up_edge, up_bracket, up_interval = _measure(
        release, "up", "CONFIRMED_PHYSICAL_UP", "RETIRED")
    actuation_id = down_measurement["actuation_id"]
    _need(down_edge.get("actuation_id") == actuation_id
          and up_measurement.get("actuation_id") == actuation_id
          and up_edge.get("actuation_id") == actuation_id,
          "down/up actuation identities differ")
    _need(down_interval[1] <= up_interval[0],
          "down/up physical state brackets overlap or reverse")

    _need(_exact_ns(down.get("admitted_ns")) and _exact_ns(down.get("input_ack_ns"))
          and down["admitted_ns"] <= down["input_ack_ns"],
          "admission/acknowledgement chronology is invalid")
    _need(down["input_ack_ns"] == down_measurement.get("sync_return_ns"),
          "admission acknowledgement differs from physical down sync")
    pre_up = up_measurement.get("pre_sample")
    post_up = up_measurement.get("post_sample")
    _need(type(pre_up) is dict and type(post_up) is dict,
          "release before/after state samples are required")
    release_request = up_measurement.get("release_request_ns")
    release_sync_return = up_measurement.get("sync_return_ns")
    _need(_exact_ns(release_request) and _exact_ns(release_sync_return)
          and _exact_ns(pre_up.get("finished_ns"))
          and _exact_ns(post_up.get("finished_ns"))
          and pre_up["finished_ns"] <= release_request <= release_sync_return
          <= post_up["finished_ns"],
          "release state samples do not bracket the explicit up operation")
    _need(up_measurement.get("release_attempted") is True,
          "release measurement lacks an attempted explicit up")

    return MeasuredReleaseBoundary(
        schema="map01-v39-perkey-tail-boundary-v1",
        program_id=down_identity[0], step=down_identity[1], key=down_identity[4],
        owner_id=down_identity[2], intent_token=down_identity[3],
        actuation_id=actuation_id, release_after_ns=up_interval[1],
        source_event_types=(down["event"], release["event"]))


class MainThreadScorerStdin(_LegacyScorerStdin):
    """Retain V1 scheduler and stdin ownership for measured release evidence."""

    def sample_measured_tail(self, *, admission_event, release_measurement,
                             backend_held_after, max_duration_ns, max_samples,
                             stop_when=None):
        if __import__("threading").get_ident() != self.owner_thread:
            raise RuntimeError("scorer tail left session main thread")
        if self.buffer:
            raise RuntimeError("scorer tail requires an empty command buffer")
        if self.eof:
            raise RuntimeError("scorer tail unavailable after command EOF")
        boundary = validate_measured_release_pair(
            admission_event, release_measurement,
            backend_held_after=backend_held_after)
        return self._sample_tail_after_boundary(
            release_after_ns=boundary.release_after_ns,
            boundary_fields={
                "release_boundary_ns": boundary.release_after_ns,
                "program_id": boundary.program_id,
                "release_step": boundary.step,
                "release_key": boundary.key,
                "owner_id": boundary.owner_id,
                "intent_token": boundary.intent_token,
                "actuation_id": boundary.actuation_id,
                "source_event_types": list(boundary.source_event_types),
                "release_evidence_schema": boundary.schema,
            },
            schema="map01-scorer-post-release-measured-tail-v1",
            max_duration_ns=max_duration_ns, max_samples=max_samples,
            stop_when=stop_when)
