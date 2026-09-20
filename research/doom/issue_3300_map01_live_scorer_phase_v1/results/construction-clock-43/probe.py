"""In-memory VIZ_Tic-entry sampling probe; trace flushes at engine exit."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import time
from pathlib import Path

import vizdoom as vd

sys.path.insert(0, "/opt/phase-probe")
import runner as phase_runner

OUT = Path("/results")
WAD = Path("/assets/freedoom2.wad")
TRACE = Path("/tmp/vizdoom-tic-entry-v2.bin")
EXPECTED_WAD = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
RECORD = struct.Struct("=QQii")

if hashlib.sha256(WAD.read_bytes()).hexdigest() != EXPECTED_WAD:
    raise SystemExit("STOP: official WAD hash mismatch")


def read_entries() -> list[dict]:
    payload = TRACE.read_bytes() if TRACE.exists() else b""
    if len(payload) % RECORD.size:
        raise RuntimeError(f"partial tic-entry record bytes: {len(payload)}")
    return [dict(zip(("pid", "monotonic_ns", "gametic", "viz_time"), RECORD.unpack_from(payload, i)))
            for i in range(0, len(payload), RECORD.size)]


rows = []
for repetition in range(3):
    TRACE.unlink(missing_ok=True)
    game = vd.DoomGame()
    row = {"repetition": repetition, "setup": "not_started", "anchors": []}
    try:
        game.set_doom_game_path(str(WAD))
        game.set_doom_scenario_path("")
        game.set_doom_map("MAP01")
        game.set_mode(vd.Mode.ASYNC_SPECTATOR)
        game.set_ticrate(35)
        game.set_seed(345401 + repetition)
        game.set_episode_timeout(35 * 60)
        game.set_window_visible(False)
        game.set_console_enabled(False)
        game.set_sound_enabled(False)
        game.set_available_buttons([])
        game.set_game_args("")
        game.init()
        game.new_episode()
        row.update(setup="initialized", mode=str(game.get_mode()),
                   ticrate=game.get_ticrate(), initial_api_tic=int(game.get_episode_time()),
                   wad_sha256=hashlib.sha256(WAD.read_bytes()).hexdigest(),
                   vizdoom_version=vd.__version__)
        begin_ns = time.monotonic_ns()
        deadline_ns = begin_ns + 1_500_000_000
        samples = []
        while time.monotonic_ns() < deadline_ns:
            start_ns = time.monotonic_ns()
            tic = int(game.get_episode_time())
            end_ns = time.monotonic_ns()
            samples.append({"start_ns": start_ns, "end_ns": end_ns, "api_tic": tic})
            time.sleep(0.05)
        row.update(passive_start_ns=begin_ns, passive_end_ns=time.monotonic_ns(),
                   samples=samples, final_api_tic=int(game.get_episode_time()))
        observed = phase_runner.ObservedGame(game)
        observed.role.name = "exact_scorer_predicate"
        row["scorer_start_ns"] = time.monotonic_ns()
        try:
            sample = phase_runner._coherent_progress_sample(observed, vd.GameVariable, 600)
            row["scorer_status"] = "returned"
            row["scorer_return"] = sample.as_dict()
        except BaseException as exc:
            row["scorer_status"] = "raised"
            row["scorer_error"] = {"type": type(exc).__name__, "message": str(exc)}
        row["scorer_end_ns"] = time.monotonic_ns()
        row["scorer_api_trace"] = observed.trace
        row["advancing_api_calls"] = 0
        post_end = time.monotonic_ns() + 150_000_000
        while time.monotonic_ns() < post_end:
            time.sleep(0.005)
        row["post_end_ns"] = time.monotonic_ns()
    except BaseException as exc:
        row["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        try:
            game.close()
            row["closed"] = True
        except BaseException as exc:
            row["closed"] = False
            row["close_error"] = {"type": type(exc).__name__, "message": str(exc)}
        try:
            row["tic_entries"] = read_entries()
        except BaseException as exc:
            row["trace_error"] = {"type": type(exc).__name__, "message": str(exc)}
        row["advancing_api_calls"] = 0
        rows.append(row)

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "raw.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
print("ENTRY_SUMMARY " + json.dumps([
    {"repetition": r["repetition"], "setup": r["setup"],
     "entries": len(r.get("tic_entries", [])), "scorer": r.get("scorer_status"),
     "closed": r.get("closed"), "api_tic": r.get("final_api_tic")}
    for r in rows
], sort_keys=True), flush=True)
