"""Scoped API-boundary fault injection for successor #2256.

This intentionally does not claim GUI, backend, timing, or actuator evidence.
It verifies only that injected session construction/dispatch failures are
reported without granting effect authority.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from runtime.cli_v1 import api
from runtime.selector_v1 import BackendUnavailable


def main() -> None:
    with patch.object(api, "open_session", side_effect=BackendUnavailable("injected backend loss")):
        result = api.dispatch({}, {}, current_observation_seq=0, current_binding_revision=0)
        assert result["status"] == "backend_unavailable", result
        assert result["schema"] == api.SCHEMA_DISPATCH, result

    class InjectedSession:
        def dispatch(self, *args, **kwargs):
            raise RuntimeError("injected dispatch fault")

    with patch.object(api, "open_session", return_value=InjectedSession()):
        result = api.dispatch({}, {}, current_observation_seq=0, current_binding_revision=0)
        assert result["status"] == "runtime_failed", result
        assert result["schema"] == api.SCHEMA_DISPATCH, result

    print("SCOPED_RUNTIME_FAULT_INJECTION_PASS cases=2 authority_grants=0")


if __name__ == "__main__":
    main()
