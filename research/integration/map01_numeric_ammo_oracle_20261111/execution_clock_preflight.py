"""No-input clock qualification for the same-host native MAP01 experiment."""
import math
import re


def require_same_host_qpc_clock(reply, local_info, before_ns, after_ns,
                                *, expected_server_instance_id=None):
    """Qualify one live sample; never translate clocks or extend an expiry.

    The caller must bracket the live MCP request using its own monotonic_ns.
    This is a same-host experimental precondition, not a cross-host clock sync,
    authorization check, or hard real-time guarantee. Keep the server instance
    ID for subsequent checks on the same connection.
    """
    if (type(reply) is not dict
            or reply.get("schema") != "agent-interface/execution-clock-v1"
            or reply.get("clock") != "time.monotonic_ns"
            or any(reply.get(key) is not False for key in
                   ("input_dispatched", "authority_granted", "lease_issued"))):
        raise ValueError("invalid clock-only response")
    instance = reply.get("server_instance_id")
    if (type(instance) is not str or re.fullmatch(r"[0-9a-f]{32}", instance) is None
            or (expected_server_instance_id is not None
                and instance != expected_server_instance_id)):
        raise ValueError("missing or replaced server instance")
    for info in (local_info, reply.get("clock_info")):
        if type(info) is not dict:
            raise ValueError("clock implementation metadata required")
        resolution = info.get("resolution")
        if (info.get("implementation") != "QueryPerformanceCounter()"
                or info.get("monotonic") is not True
                or info.get("adjustable") is not False
                or type(resolution) not in (int, float)
                or not math.isfinite(resolution) or not 0 < resolution <= 1e-6):
            raise ValueError("same-host high-resolution QPC clock required")
    sample = reply.get("monotonic_ns")
    if (any(type(value) is not int for value in (before_ns, after_ns, sample))
            or not 0 < before_ns <= sample <= after_ns):
        raise ValueError("server clock sample is outside the live local bracket")
    return {"status": "qualified", "sample_ns": sample,
            "server_instance_id": instance, "input_dispatched": False,
            "clock_info": dict(reply["clock_info"]),
            "request_before_ns": before_ns, "response_after_ns": after_ns,
            "scope": "same-host clock precondition only; no authority or latency bound"}
