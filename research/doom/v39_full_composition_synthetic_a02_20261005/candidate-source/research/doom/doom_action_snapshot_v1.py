"""Build generic action-validity snapshots from one exact DOOM observation."""
from action_validity_admission_v1 import CONTRACT_FORMAT, SNAPSHOT_FORMAT


SUPPORTED = {"health", "ammo"}


def build_action_snapshot(observation, contract, readers):
    if (type(observation) is not dict or type(contract) is not dict or
            contract.get("format") != CONTRACT_FORMAT or
            type(contract.get("source")) is not dict or
            type(contract["source"].get("signals")) is not dict):
        raise ValueError("exact observation and action contract required")
    required = set(contract["source"]["signals"])
    if not required or not required <= SUPPORTED or set(readers) != required:
        raise ValueError("exact required DOOM signal readers required")
    sequence = observation.get("sequence")
    capture_ns = observation.get("capture_ns")
    binding = observation.get("pointer_binding")
    signals = {}
    for signal_id in sorted(required):
        result = readers[signal_id].read(observation)
        if (type(result) is not dict or result.get("signal_id") != signal_id or
                result.get("sequence") != sequence or
                result.get("capture_ns") != capture_ns or
                result.get("binding") != binding or
                result.get("status") not in ("observed", "unknown") or
                (result.get("status") == "unknown" and result.get("value") is not None)):
            raise ValueError("signal reader must bind the exact observation epoch")
        signals[signal_id] = {"status": result["status"], "value": result["value"]}
    return {"format": SNAPSHOT_FORMAT, "sequence": sequence,
            "capture_ns": capture_ns, "binding": binding, "signals": signals}
