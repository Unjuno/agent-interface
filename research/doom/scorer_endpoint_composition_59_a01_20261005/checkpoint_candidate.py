"""Prospective coherent scorer checkpoint; controller receives status only."""
from __future__ import annotations

import math
import time
from numbers import Real


PENDING = "REFRESH_RETURNED_RUNTIME_QUALIFICATION_PENDING"


def checkpoint(game, executor, owner, variables, log_path, checkpoint_id):
    """Refresh and retain one coherent endpoint snapshot without input authority.

    ``variables`` is an insertion-ordered mapping of public names to ViZDoom
    GameVariable values. The private log contains the score snapshot; the
    controller-facing receipt never does.
    """
    row = {
        "schema": "private-score-checkpoint-v2-candidate",
        "id": checkpoint_id,
        "started_ns": time.perf_counter_ns(),
        "status": "UNKNOWN",
        "grants_input_authority": False,
    }
    try:
        with executor.lock:
            if executor.closed or executor.active is not None:
                raise ValueError("scoring requires idle open executor")
            owner_state = owner.call("input_state")
            if (owner_state["owned_keycodes"] or owner_state["owned_buttons"] or
                    owner_state["active_lease_deadline_ns"] is not None):
                raise ValueError("owner is not neutral")
            row["owner_state"] = owner_state
            if game.is_episode_finished():
                raise ValueError("finished episode cannot refresh")

            row["refresh_before_ns"] = time.perf_counter_ns()
            row["tic_before"] = game.get_episode_time()
            game.advance_action(1, True)
            row["refresh_after_ns"] = time.perf_counter_ns()
            row["tic_after"] = game.get_episode_time()
            before, after = row["tic_before"], row["tic_after"]
            if (type(before) is not int or type(after) is not int or
                    before < 0 or after <= before):
                raise ValueError("refresh did not acknowledge tic progress")
            row["tic_delta"] = after - before

            state = game.get_state()
            if state is None or type(state.tic) is not int or state.tic != after:
                raise ValueError("snapshot tic does not match acknowledged endpoint")
            raw_values = state.game_variables
            names = list(variables)
            if list(game.get_available_game_variables()) != list(variables.values()):
                raise ValueError("configured game-variable order does not match mapping")
            if len(raw_values) != len(names) or len(set(names)) != len(names):
                raise ValueError("snapshot variable shape is invalid")
            values = {}
            for name, value in zip(names, raw_values):
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("snapshot variable name is invalid")
                if isinstance(value, bool) or not isinstance(value, Real):
                    raise ValueError("snapshot score value is invalid")
                numeric_value = float(value)
                if not math.isfinite(numeric_value):
                    raise ValueError("snapshot score value is invalid")
                values[name] = numeric_value
            row["values"] = values
            row["state_tic"] = state.tic
            row["read_finished_ns"] = time.perf_counter_ns()
            row["tic_after_read"] = game.get_episode_time()
            readback_tic = row["tic_after_read"]
            if type(readback_tic) is not int or readback_tic != after:
                raise ValueError("episode tic changed during snapshot read")
            row["status"] = PENDING
    except Exception as error:
        row.pop("values", None)
        row["error"] = repr(error)
    finally:
        row["finished_ns"] = time.perf_counter_ns()
        with log_path.open("a", encoding="utf-8") as log:
            import json
            log.write(json.dumps(row, sort_keys=True) + "\n")
    return {"checkpoint_id": checkpoint_id, "status": row["status"]}
