from __future__ import annotations

import base64
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import time

from Xlib import X, display

from native_handle_bridge_v1 import NativeHandleBridge
from xid_fixture import EFFECT_ATOM, TARGET_GEOMETRY, fixture
from xres_identity_guard_3575 import owner_identity, permits


ROOT = Path("/results")
OUT = ROOT / "bridge"


def start_fixture(ctx, label):
    parent, child = ctx.Pipe(duplex=False)
    stop = ctx.Event()
    process = ctx.Process(target=fixture, args=(child, stop), name=label)
    process.start()
    child.close()
    info = parent.recv()
    info["label"] = label
    info["start_observed_ns"] = time.monotonic_ns()
    return info, process, stop, parent


def window_pixels(d, xid):
    window = d.create_resource_object("window", xid)
    geometry = window.get_geometry()
    image = window.get_image(0, 0, geometry.width, geometry.height,
                             X.ZPixmap, 0xFFFFFFFF)
    data = bytes(image.data)
    return {"size": [geometry.width, geometry.height], "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "base64": base64.b64encode(data).decode("ascii")}


def effect_property(xid):
    d = display.Display()
    window = d.create_resource_object("window", xid)
    atom = d.intern_atom(EFFECT_ATOM)
    card = d.intern_atom("CARDINAL")
    prop = window.get_full_property(atom, card)
    values = [] if prop is None else [int(v) for v in prop.value]
    d.sync()
    d.close()
    return values


def image_manifest():
    return [{"path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(OUT.rglob("*.png"))]


def main():
    if ROOT.exists() and any(ROOT.iterdir()):
        raise RuntimeError("formal results directory is not empty")
    ctx = mp.get_context("fork")
    p1_info, p1_proc, p1_stop, p1_pipe = start_fixture(ctx, "p1")
    bridge = None
    p2 = None
    raw = {"allocation_id": "issue3575-xres-guard-formal-01", "issue": 3575,
           "mode": "formal-one-shot", "repo_source_commit": os.environ["OBSTAC_SOURCE_COMMIT"],
           "container_image_id": os.environ["OBSTAC_IMAGE_ID"],
           "freeze_sha256": os.environ["OBSTAC_FREEZE_SHA256"],
           "source_manifest_sha256": hashlib.sha256(Path("/source_manifest.json").read_bytes()).hexdigest(),
           "old_guard_decisions": 0, "bridge_old_click_invocations": 0,
           "fresh_control_attempts": 0, "p1": p1_info}
    try:
        bridge = NativeHandleBridge(os.environ["DISPLAY"], {"fixture": p1_info["xid"]},
                                    "fixture", OUT)
        obs1 = bridge.observe()
        old_mint = bridge.mint("old_alias", obs1["sequence"], [109, 118])
        id_display = display.Display()
        owner_p1 = owner_identity(id_display, p1_info["xid"])
        id_display.close()
        raw["p1_observation"] = obs1
        raw["old_handle"] = {"mint": old_mint, "point": [109, 118],
                             "owner_identity": owner_p1}
        raw["p1_identity_matches_fixture"] = (
            owner_p1["pid"] == p1_info["pid"] and
            owner_p1["pid_start_ticks"] == p1_info["pid_start_ticks"])

        p1_stop.set()
        p1_proc.join(5)
        raw["p1_cleanup"] = {"exit_observed": not p1_proc.is_alive(),
                             "exit_code": p1_proc.exitcode}
        p1_pipe.close()
        if p1_proc.is_alive():
            raise RuntimeError("p1 did not exit")

        p2_info, p2_proc, p2_stop, p2_pipe = start_fixture(ctx, "p2")
        p2 = (p2_info, p2_proc, p2_stop, p2_pipe)
        raw["p2"] = p2_info
        id_display = display.Display()
        owner_p2 = owner_identity(id_display, p2_info["xid"])
        pixels_p1 = window_pixels(id_display, p1_info["xid"])
        pixels_p2 = window_pixels(id_display, p2_info["xid"])
        id_display.close()
        raw["p2_owner_identity"] = owner_p2
        raw["independent_window_pixels"] = {"p1": pixels_p1, "p2": pixels_p2,
             "pixel_identical": pixels_p1["base64"] == pixels_p2["base64"]}
        raw["preconditions"] = {
            "same_xid": p1_info["xid"] == p2_info["xid"],
            "distinct_pid": p1_info["pid"] != p2_info["pid"],
            "distinct_start_ticks": p1_info["pid_start_ticks"] != p2_info["pid_start_ticks"],
            "p1_exit_observed": raw["p1_cleanup"]["exit_observed"],
            "p1_xres_matches_fixture": raw["p1_identity_matches_fixture"],
            "p2_xres_matches_fixture": (owner_p2["pid"] == p2_info["pid"] and
                                         owner_p2["pid_start_ticks"] == p2_info["pid_start_ticks"]),
            "same_geometry": p1_info["geometry"] == p2_info["geometry"],
            "pixel_identical": pixels_p1["size"] == [240, 160] and
                               pixels_p2["size"] == [240, 160] and
                               pixels_p1["base64"] == pixels_p2["base64"],
        }
        if not all(raw["preconditions"].values()):
            raw["decision"] = "HOLD_FORMAL_PRECONDITION_NOT_MET"
            return raw

        before_old = bridge.backend.emissions
        raw["old_guard_decisions"] = 1
        old_permitted, old_reason = permits(owner_p1, owner_p2)
        before_effect = effect_property(p2_info["xid"])
        old_result = None
        if old_permitted:
            raw["bridge_old_click_invocations"] = 1
            old_result = bridge.click("old_alias", old_mint, tail=())
        after_old = bridge.backend.emissions
        after_effect = effect_property(p2_info["xid"])
        raw["old_alias_guard"] = {"permitted": old_permitted, "reason": old_reason,
             "bridge_click_invoked": raw["bridge_old_click_invocations"] == 1,
             "emissions_before": before_old, "emissions_after": after_old,
             "effect_before": before_effect, "effect_after": after_effect,
             "bridge_result": old_result}
        if old_permitted:
            # The single stale-alias decision was unsafe. Do not run a second
            # action against p2; preserve the independent effect as observed.
            raw["decision"] = (
                "FAIL_GENERATION_GUARD_DID_NOT_REJECT_STALE_ALIAS"
                if old_result and old_result.get("status") == "completed"
                and after_old > before_old and after_effect == [1, 109, 118]
                else "HOLD_OR_STOP_UNCLASSIFIED")
            return raw

        obs2 = bridge.observe()
        fresh_mint = bridge.mint("fresh_alias", obs2["sequence"], [212, 118])
        identity_display = display.Display()
        fresh_identity = owner_identity(identity_display, p2_info["xid"])
        identity_display.close()
        fresh_permitted, fresh_reason = permits(fresh_identity, owner_p2)
        raw["fresh_control_attempts"] = 1
        before_fresh = bridge.backend.emissions
        fresh_result = bridge.click("fresh_alias", fresh_mint, tail=()) if fresh_permitted else None
        time.sleep(0.03)
        fresh_effect = effect_property(p2_info["xid"])
        raw["fresh_control"] = {"permitted": fresh_permitted, "reason": fresh_reason,
             "current_owner_identity": fresh_identity,
             "mint": fresh_mint, "result": fresh_result,
             "emissions_before": before_fresh, "emissions_after": bridge.backend.emissions,
             "effect": fresh_effect}
        raw["decision"] = (
            "PASS_GENERATION_GUARD_REJECTED_STALE_ALIAS"
            if not old_permitted and old_reason == "PROCESS_INCARNATION_MISMATCH"
            and raw["bridge_old_click_invocations"] == 0 and after_old == before_old
            and before_effect == [0, 0, 0] and after_effect == [0, 0, 0]
            and fresh_permitted and fresh_result and fresh_result.get("status") == "completed"
            and bridge.backend.emissions - before_fresh == 3 and fresh_effect == [1, 212, 118]
            else "FAIL_GENERATION_GUARD_DID_NOT_REJECT_STALE_ALIAS"
            if old_permitted and raw["bridge_old_click_invocations"] == 1
            and old_result and old_result.get("status") == "completed"
            and after_old > before_old and after_effect == [1, 109, 118]
            else "HOLD_OR_STOP_UNCLASSIFIED")
        return raw
    finally:
        if p2:
            p2[2].set(); p2[1].join(5); p2[3].close()
            raw["p2_cleanup"] = {"exit_observed": not p2[1].is_alive(), "exit_code": p2[1].exitcode}
            if p2[1].is_alive(): p2[1].terminate(); p2[1].join(2)
        if p1_proc.is_alive():
            p1_stop.set(); p1_proc.join(3)
            if p1_proc.is_alive(): p1_proc.terminate(); p1_proc.join(2)
        if bridge:
            bridge.close(); raw["bridge_closed"] = True
        raw["images"] = image_manifest()
        (ROOT / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
