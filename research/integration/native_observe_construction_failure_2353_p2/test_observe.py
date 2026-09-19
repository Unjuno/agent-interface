import json
from unittest.mock import patch

from runtime.cli_v1 import observe as observe_api
from runtime.selector_v1 import BackendUnavailable


def valid_call():
    return observe_api.observe(
        {}, target="fixture", frame="window_client",
        region=[0, 0, 10, 10],
    )


def main():
    with patch.object(observe_api, "open_session", side_effect=RuntimeError("X11BackendError: XTEST unavailable")):
        failed = valid_call()
    assert failed["status"] == "observation_failed"
    assert "XTEST unavailable" in failed["error"]
    assert failed["side_effect_authority"] is False
    assert failed["input_dispatched"] is False

    with patch.object(observe_api, "open_session", side_effect=BackendUnavailable("no backend")):
        unavailable = valid_call()
    assert unavailable["status"] == "backend_unavailable"
    assert unavailable["input_dispatched"] is False

    class Backend:
        def observe_read_only(self, target, frame, region):
            return {"target": target, "frame": frame, "region": region}
        def close(self):
            self.closed = True

    class Session:
        backend = Backend()

    with patch.object(observe_api, "open_session", return_value=Session()):
        returned = valid_call()
    assert returned["status"] == "returned"
    assert returned["observation"]["target"] == "fixture"
    print(json.dumps({
        "status": "PASS_NATIVE_OBSERVE_CONSTRUCTION_FAILURE_SCOPED",
        "cases": 3,
        "authority_grants": 0,
        "input_calls": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
