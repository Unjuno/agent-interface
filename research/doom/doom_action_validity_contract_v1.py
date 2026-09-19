"""Bind a small planner-authored MAP01 validity spec to exact local signals."""
from action_validity_admission_v1 import (
    CONTRACT_FORMAT, action_fingerprint)


FIRE_ACTIONS = {"fire", "advance_fire", "retreat_fire"}
FIELDS = {"critical_health_minimum", "maximum_health_loss",
          "minimum_ammo", "max_current_age_ms"}


def _observed(signal, signal_id):
    if (type(signal) is not dict or signal.get("format") != "observable-signal-v1" or
            signal.get("status") != "observed" or signal.get("signal_id") != signal_id or
            type(signal.get("value")) is not int or signal["value"] < 0 or
            type(signal.get("sequence")) is not int or
            type(signal.get("capture_ns")) is not int or
            type(signal.get("binding")) is not dict):
        raise ValueError(f"exact observed {signal_id} source signal required")
    return signal


def build_contract(commands, authored, health_signal, ammo_signal=None):
    """Validate planner semantics and produce a generic no-authority contract."""
    if (type(commands) is not list or not commands or
            any(type(command) is not dict or set(command) != {"action", "extent"}
                for command in commands)):
        raise ValueError("nonempty exact MAP01 commands required")
    if type(authored) is not dict or set(authored) != FIELDS:
        raise ValueError("exact planner-authored action validity required")
    critical = authored["critical_health_minimum"]
    loss = authored["maximum_health_loss"]
    minimum_ammo = authored["minimum_ammo"]
    age = authored["max_current_age_ms"]
    if (type(critical) is not int or not 1 <= critical <= 200 or
            type(loss) is not int or not 0 <= loss <= 20 or
            type(minimum_ammo) is not int or not 0 <= minimum_ammo <= 200 or
            type(age) is not int or not 100 <= age <= 1000):
        raise ValueError("authored action validity exceeds bounded schema semantics")
    uses_fire = any(command["action"] in FIRE_ACTIONS for command in commands)
    if uses_fire and minimum_ammo < 1:
        raise ValueError("fire actions require a positive ammunition predicate")
    if not uses_fire and minimum_ammo != 0:
        raise ValueError("non-fire actions must not add an ammunition dependency")
    health = _observed(health_signal, "health")
    signals = {"health": {"status": "observed", "value": health["value"]}}
    predicates = [
        {"signal_id": "health", "operator": "minimum", "value": critical},
        {"signal_id": "health", "operator": "max_decrease_from_source",
         "value": loss}]
    if uses_fire:
        ammo = _observed(ammo_signal, "ammo")
        if (ammo["sequence"] != health["sequence"] or
                ammo["capture_ns"] != health["capture_ns"] or
                ammo["binding"] != health["binding"]):
            raise ValueError("health and ammo must share one observation epoch")
        signals["ammo"] = {"status": "observed", "value": ammo["value"]}
        predicates.append({"signal_id": "ammo", "operator": "minimum",
                           "value": minimum_ammo})
    return {"format": CONTRACT_FORMAT,
            "action_fingerprint": action_fingerprint(commands),
            "source": {"sequence": health["sequence"],
                       "capture_ns": health["capture_ns"],
                       "binding": health["binding"], "signals": signals},
            "max_current_age_ms": age, "predicates": predicates}
