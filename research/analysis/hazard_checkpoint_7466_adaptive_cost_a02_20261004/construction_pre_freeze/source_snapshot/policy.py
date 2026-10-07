#!/usr/bin/env python3
"""Streaming adaptive policy. Reads only current/past public observations on stdin."""
import json
import math
import sys


def send(obj):
    print(json.dumps(obj, sort_keys=True, separators=(",", ":")), flush=True)


def recv():
    line = sys.stdin.readline()
    if not line:
        raise EOFError("protocol ended")
    return json.loads(line)


config = recv()
if config.get("type") != "CALIBRATION":
    raise SystemExit("missing calibration")
prob = config["p_by_signal"]
base = config["base_rate"]
calibrated = bool(config["calibration_pass"])
send({"type": "READY", "calibrated": calibrated})

while True:
    msg = recv()
    if msg.get("type") == "QUIT":
        break
    if msg.get("type") != "START":
        raise SystemExit("expected START")
    send({"type": "START_ACK"})
    llr, nobs, active = 0.0, 0, calibrated
    while True:
        tick = recv()
        if tick.get("type") == "END":
            send({"type": "END_ACK", "active": active, "nobs": nobs, "llr": round(llr, 9)})
            break
        if tick.get("type") != "TICK":
            raise SystemExit("expected TICK or END")
        symbol = tick["signal"]
        p = prob.get(symbol)
        if active and p is not None and tick["legal"] and tick["age"] > 0:
            checkpoint = p * tick["age"] * tick["replay_cost"] > tick["checkpoint_cost"]
        else:
            checkpoint = bool(tick["legal"] and tick["progress"] >= tick["next_event"])
        send({"type": "DECISION", "checkpoint": bool(checkpoint), "adaptive_active": bool(active), "p": p})
        feedback = recv()
        if feedback.get("type") != "FEEDBACK" or feedback.get("signal") != symbol:
            raise SystemExit("feedback mismatch")
        y = int(feedback["interrupted"])
        nobs += 1
        if p is not None and 0.0 < p < 1.0 and 0.0 < base < 1.0:
            llr += y * math.log(p / base) + (1 - y) * math.log((1 - p) / (1 - base))
        if active and nobs >= 24 and llr < -3.0:
            active = False
        send({"type": "OBSERVED", "adaptive_active": bool(active), "nobs": nobs, "llr": round(llr, 9)})
