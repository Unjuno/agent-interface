#!/usr/bin/env python3
"""Frozen synthetic counterfactual-intent width experiment; no action I/O."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

torch.set_num_threads(1)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass
torch.use_deterministic_algorithms(True)

ALLOCATION = "needle-intent-capacity-4679-v2"
SEEDS = (4153201, 4153203, 4153207)
INTENTS = ("TRACK", "STABILIZE", "WATCH_ONLY", "OUT_OF_SCOPE")
CLASSES = ("CONTINUE", "CORRECT", "WATCH", "YIELD")
CLASS_ID = {name: index for index, name in enumerate(CLASSES)}
INTENT_ID = {name: index for index, name in enumerate(INTENTS)}
TRAIN_BASES = 4096
HELDOUT_BASES = 2048
STEPS = 900
LR = 0.006
WEIGHT_DECAY = 1e-4
WIDTH_REFERENCE = 24
WIDTH_CANDIDATE = 64
INVALID_INTENTS = (None, "", "UNKNOWN", "track", 7, False)


def canonical_sha(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def gen_states(count, seed):
    generator = torch.Generator(device="cpu").manual_seed(seed)
    dx = torch.empty(count).uniform_(-0.16, 0.16, generator=generator)
    dy = torch.empty(count).uniform_(-0.12, 0.12, generator=generator)
    vx = torch.empty(count).uniform_(-0.10, 0.10, generator=generator)
    vy = torch.empty(count).uniform_(-0.10, 0.10, generator=generator)
    confidence = torch.empty(count).uniform_(0.55, 1.0, generator=generator)
    visible = (torch.rand(count, generator=generator) > 0.08).float()
    return torch.stack((dx, dy, vx, vy, confidence, visible), dim=1)


def teacher(state, intent):
    dx, dy, vx, vy, confidence, visible = (float(x) for x in state)
    speed = abs(vx) + abs(vy)
    if intent == "OUT_OF_SCOPE":
        return CLASS_ID["YIELD"]
    if intent == "WATCH_ONLY":
        return CLASS_ID["WATCH"] if visible >= 0.5 else CLASS_ID["YIELD"]
    if visible < 0.5 or confidence < 0.62:
        return CLASS_ID["YIELD"]
    if intent == "TRACK":
        if confidence < 0.74:
            return CLASS_ID["WATCH"]
        if abs(dx) > 0.065 or abs(dy) > 0.085:
            return CLASS_ID["CORRECT"]
        return CLASS_ID["CONTINUE"]
    if intent == "STABILIZE":
        if confidence < 0.80:
            return CLASS_ID["WATCH"]
        if speed > 0.105 or abs(dx) > 0.035:
            return CLASS_ID["CORRECT"]
        return CLASS_ID["CONTINUE"]
    raise ValueError(f"unknown intent: {intent!r}")


def labels_for(states):
    return [[teacher(state, intent) for intent in INTENTS] for state in states]


def expand(states, intent_aware):
    features = []
    labels = []
    for state in states:
        for intent_index, intent in enumerate(INTENTS):
            if intent_aware:
                one_hot = torch.zeros(len(INTENTS), dtype=torch.float32)
                one_hot[intent_index] = 1.0
                features.append(torch.cat((state, one_hot)))
            else:
                features.append(state.clone())
            labels.append(teacher(state, intent))
    return torch.stack(features), torch.tensor(labels, dtype=torch.long)


def resolve_intent(intent):
    """Interface gate: malformed/unknown IDs YIELD without invoking the model."""
    if not isinstance(intent, str) or intent not in INTENT_ID:
        return {"decision": "YIELD", "model_calls": 0}
    return {"decision": "VALID_INTENT", "model_calls": 0}


class Net(nn.Module):
    def __init__(self, input_dim, width):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, width), nn.Tanh(),
            nn.Linear(width, width), nn.Tanh(),
            nn.Linear(width, len(CLASSES)),
        )

    def forward(self, value):
        return self.net(value)


def parameter_count(input_dim, width):
    return (input_dim * width + width) + (width * width + width) + (width * len(CLASSES) + len(CLASSES))


def prepare_output(path):
    """Accept a pre-created empty Docker bind mount, but never overwrite data."""
    path = Path(path)
    if path.exists():
        if not path.is_dir():
            raise SystemExit("STOP_OUTPUT_NOT_DIRECTORY")
        if next(path.iterdir(), None) is not None:
            raise SystemExit("STOP_OUTPUT_NOT_EMPTY")
    else:
        path.mkdir(parents=True)
    return path


def fit(train_x, train_y, input_dim, width, model_seed):
    torch.manual_seed(model_seed)
    model = Net(input_dim, width)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    started = time.perf_counter_ns()
    for _ in range(STEPS):
        optimizer.zero_grad(set_to_none=True)
        loss = F.cross_entropy(model(train_x), train_y)
        loss.backward()
        optimizer.step()
    elapsed = time.perf_counter_ns() - started
    state = {name: tensor.detach().cpu().tolist() for name, tensor in model.state_dict().items()}
    return model, state, elapsed


def run_seed(seed):
    train_states_t = gen_states(TRAIN_BASES, seed)
    heldout_states_t = gen_states(HELDOUT_BASES, seed + 1)
    train_states = train_states_t.tolist()
    heldout_states = heldout_states_t.tolist()
    arms = {}
    specifications = (
        ("STATE_ONLY_24", False, WIDTH_REFERENCE, seed + 10),
        ("INTENT_AWARE_24", True, WIDTH_REFERENCE, seed + 20),
        ("INTENT_AWARE_64", True, WIDTH_CANDIDATE, seed + 20),
    )
    for name, intent_aware, width, model_seed in specifications:
        train_x, train_y = expand(train_states_t, intent_aware)
        heldout_x, heldout_y = expand(heldout_states_t, intent_aware)
        input_dim = 10 if intent_aware else 6
        model, model_state, elapsed = fit(train_x, train_y, input_dim, width, model_seed)
        with torch.no_grad():
            predictions = model(heldout_x).argmax(dim=1).tolist()
        controls = [resolve_intent(value) for value in INVALID_INTENTS]
        arms[name] = {
            "intent_aware": intent_aware,
            "input_dim": input_dim,
            "width": width,
            "model_seed": model_seed,
            "fit_steps": STEPS,
            "fit_ns": elapsed,
            "parameter_count": parameter_count(input_dim, width),
            "model_state": model_state,
            "model_state_sha256": canonical_sha(model_state),
            "predictions": predictions,
            "invalid_intent_controls": controls,
        }
    return {
        "schema": "needle-intent-capacity.raw.v1",
        "allocation": ALLOCATION,
        "seed": seed,
        "constants": {
            "train_base_states": TRAIN_BASES,
            "heldout_base_states": HELDOUT_BASES,
            "intents": list(INTENTS),
            "classes": list(CLASSES),
            "steps": STEPS,
            "lr": LR,
            "weight_decay": WEIGHT_DECAY,
            "reference_width": WIDTH_REFERENCE,
            "candidate_width": WIDTH_CANDIDATE,
        },
        "train_states": train_states,
        "heldout_states": heldout_states,
        "train_labels_by_state": labels_for(train_states_t),
        "heldout_labels_by_state": labels_for(heldout_states_t),
        "arms": arms,
        "authority": False,
        "action_emissions": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal", action="store_true", help="required before any optimizer step")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.formal:
        raise SystemExit("construction-only by default; pass --formal for the single preregistered allocation")
    out = prepare_output(Path(args.out))
    for seed in SEEDS:
        result = run_seed(seed)
        path = out / f"seed_{seed}.json"
        serialized = json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        path.write_text(serialized, encoding="utf-8", newline="\n")
        print(json.dumps({"seed": seed, "arms": len(result["arms"]), "fit_count": len(result["arms"]),
                          "fit_steps_each": STEPS, "raw_bytes": path.stat().st_size,
                          "raw_sha256": hashlib.sha256(serialized.encode()).hexdigest()}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
