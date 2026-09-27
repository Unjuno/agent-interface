"""Receipt-gated composition of learned role adapters as one reusable skill graph."""
import base64, copy, gzip, hashlib, io, json, math, platform, random, statistics, time
import torch
from torch import nn

SEED = 3775
D, H, C, RANK = 8, 16, 4, 2
N_BASE, N_SUPPORT, N_HELDOUT = 512, 16, 4096
BASE_STEPS, ADAPTER_STEPS = 400, 120
LR_BASE, LR_ADAPTER = 0.025, 0.04
SCOPE = "synthetic-fixture-v1"

def data(n, seed):
    return torch.randn(n, D, generator=torch.Generator(device="cpu").manual_seed(seed))

def labels(x, role):
    a = (x[:, 0] > 0).long()
    b = (x[:, 1] > 0).long()
    if role == "B":
        a = 1 - a
    elif role == "C":
        b = 1 - b
    return a * 2 + b

class Core(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(D, H), nn.Tanh())
        self.head = nn.Linear(H, C)
    def forward(self, x):
        return self.head(self.enc(x))

class LoRA(nn.Module):
    def __init__(self, core):
        super().__init__()
        self.core = core
        for p in core.parameters():
            p.requires_grad_(False)
        self.a = nn.Parameter(torch.randn(H, RANK) * 0.04)
        self.b = nn.Parameter(torch.zeros(RANK, C))
    def forward(self, x):
        h = self.core.enc(x)
        return self.core.head(h) + (h @ self.a @ self.b) / RANK

def clone_state(model):
    return {k: v.detach().clone() for k, v in model.state_dict().items()}

def exact_state(model, ref):
    now = model.state_dict()
    return list(now) == list(ref) and all(
        now[k].dtype == ref[k].dtype and now[k].shape == ref[k].shape
        and torch.equal(now[k], ref[k]) for k in ref
    )

def train(model, x, y, params, steps, lr, seed):
    opt = torch.optim.AdamW(params, lr=lr)
    rng = torch.Generator(device="cpu").manual_seed(seed)
    model.train()
    started = time.perf_counter_ns()
    for _ in range(steps):
        ix = torch.randint(len(x), (32,), generator=rng)
        loss = nn.functional.cross_entropy(model(x[ix]), y[ix])
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    return (time.perf_counter_ns() - started) / 1e6

def prediction_rows(model, x, y):
    model.eval()
    with torch.no_grad():
        preds = model(x).argmax(-1)
    expected = y.tolist()
    predicted = preds.tolist()
    correct = sum(a == b for a, b in zip(expected, predicted))
    # Losslessly pack two 4-bit (expected,predicted) pairs into each byte.
    nibbles = [(a << 2) | b for a, b in zip(expected, predicted)]
    packed = bytes((nibbles[i] << 4) | nibbles[i + 1]
                   for i in range(0, len(nibbles), 2))
    return {"n": len(expected), "correct": correct, "accuracy": correct / len(expected),
            "packed_pairs_b64": base64.b64encode(packed).decode(),
            "packed_pairs_sha256": hashlib.sha256(packed).hexdigest()}

def version_of(role):
    return {"A": "base-v1", "B": "adapter-B-v1", "C": "adapter-C-v1"}[role]

def receipt(source, target, generation, receipt_id, source_version=None,
            verified=True, scope=SCOPE):
    return {
        "source_role": source,
        "target_role": target,
        "generation": generation,
        "receipt_id": receipt_id,
        "source_version": source_version or version_of(source),
        "verified": verified,
        "scope": scope,
        "issuer": "independent_fixture_oracle",
    }

class SkillGraph:
    def __init__(self, nodes, generation=1):
        self.nodes = nodes
        self.generation = generation
        self.current = "A"
        self.edges = {"A": ("B",), "B": ("C",), "C": ()}
        self.accepted_receipts = set()
        self.transition_log = []

    def dispatch(self, requested_role, generation):
        if generation != self.generation or requested_role != self.current:
            return "YIELD", None
        model = self.nodes.get(requested_role)
        return ("PROPOSE", model) if model is not None else ("YIELD", None)

    def transition(self, r):
        source = r.get("source_role")
        target = r.get("target_role")
        valid = (
            source == self.current
            and target in self.edges.get(self.current, ())
            and r.get("generation") == self.generation
            and r.get("receipt_id") not in self.accepted_receipts
            and r.get("source_version") == version_of(self.current)
            and r.get("verified") is True
            and r.get("scope") == SCOPE
            and r.get("issuer") == "independent_fixture_oracle"
        )
        if not valid:
            return "YIELD"
        self.accepted_receipts.add(r["receipt_id"])
        self.transition_log.append({"from": source, "to": target,
                                    "generation": self.generation,
                                    "receipt_id": r["receipt_id"]})
        self.current = target
        return "ADVANCE"

    def state(self):
        return (self.current, self.generation, tuple(sorted(self.accepted_receipts)),
                tuple((e["from"], e["to"], e["generation"], e["receipt_id"])
                      for e in self.transition_log))

def main():
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(SEED)
    torch.manual_seed(SEED)

    xa, xb, xc, ea, eb, ec = [
        data(n, SEED + i) for i, n in enumerate(
            (N_BASE, N_SUPPORT, N_SUPPORT, N_HELDOUT, N_HELDOUT, N_HELDOUT),
            start=1)
    ]
    ya, yb, yc = labels(xa, "A"), labels(xb, "B"), labels(xc, "C")
    eya, eyb, eyc = labels(ea, "A"), labels(eb, "B"), labels(ec, "C")

    base = Core()
    base_train_ms = train(base, xa, ya, list(base.parameters()), BASE_STEPS,
                          LR_BASE, SEED + 10)
    base_before = clone_state(base)

    template = LoRA(base)
    initial = clone_state(template)
    adapter_b, adapter_c = LoRA(base), LoRA(base)
    adapter_b.load_state_dict(initial)
    adapter_c.load_state_dict(initial)
    b_train_ms = train(adapter_b, xb, yb, [adapter_b.a, adapter_b.b],
                       ADAPTER_STEPS, LR_ADAPTER, SEED + 11)
    c_train_ms = train(adapter_c, xc, yc, [adapter_c.a, adapter_c.b],
                       ADAPTER_STEPS, LR_ADAPTER, SEED + 12)

    nodes = {"A": base, "B": adapter_b, "C": adapter_c}
    graph = SkillGraph(nodes, generation=1)
    flat_rows, graph_rows = {}, {}
    for role, x, y in (("A", ea, eya), ("B", eb, eyb), ("C", ec, eyc)):
        flat_rows[role] = prediction_rows(nodes[role], x, y)

    # Seven invalid transition classes must not mutate the active graph.
    bad = {
        "unknown_destination": receipt("A", "Z", 1, "bad-unknown"),
        "skipped_A_to_C": receipt("A", "C", 1, "bad-skip"),
        "wrong_source_node": receipt("B", "C", 1, "bad-source"),
        "stale_generation": receipt("A", "B", 0, "bad-stale"),
        "wrong_adapter_version": receipt("A", "B", 1, "bad-version",
                                         source_version="base-v0"),
        "unverified_outcome": receipt("A", "B", 1, "bad-unverified",
                                      verified=False),
        "wrong_scope": receipt("A", "B", 1, "bad-scope", scope="other-scope"),
    }
    controls = {}
    initial_graph_state = graph.state()
    for name, item in bad.items():
        before = graph.state()
        decision = graph.transition(item)
        controls[name] = {"decision": decision,
                          "state_unchanged": graph.state() == before == initial_graph_state}
    assert all(c["decision"] == "YIELD" and c["state_unchanged"]
               for c in controls.values())

    # Duplicate-ID behavior is tested on a separate probe graph so it remains
    # testable even if learned competence later fails to yield a valid receipt.
    duplicate_probe = SkillGraph(nodes, generation=1)
    duplicate_receipt = receipt("A", "B", 1, "duplicate-probe")
    duplicate_first = duplicate_probe.transition(duplicate_receipt)
    duplicate_state = duplicate_probe.state()
    duplicate_second = duplicate_probe.transition(duplicate_receipt)
    controls["duplicate_receipt"] = {
        "first_decision": duplicate_first,
        "decision": duplicate_second,
        "state_unchanged": duplicate_probe.state() == duplicate_state,
    }
    assert duplicate_first == "ADVANCE" and duplicate_second == "YIELD"
    assert controls["duplicate_receipt"]["state_unchanged"]

    # The graph evaluates roles in sequence. Each fixture receipt is emitted
    # only if a preselected held-out row has the exact oracle label.
    graph_execution = []
    sequence = (("A", ea, eya, "B"), ("B", eb, eyb, "C"), ("C", ec, eyc, None))
    for role, x, y, next_role in sequence:
        decision, chosen = graph.dispatch(role, generation=1)
        if decision != "PROPOSE":
            graph_execution.append({"role": role, "decision": decision})
            break
        rows = prediction_rows(chosen, x, y)
        graph_rows[role] = rows
        assert flat_rows[role]["packed_pairs_sha256"] == rows["packed_pairs_sha256"]
        event = {"role": role, "decision": decision,
                 "fixed_first_row_effect_verified":
                    (base64.b64decode(rows["packed_pairs_b64"])[0] >> 6) == ((base64.b64decode(rows["packed_pairs_b64"])[0] >> 4) & 3)}
        if next_role is not None:
            item = receipt(role, next_role, 1, "effect-" + role + "-g1",
                           verified=event["fixed_first_row_effect_verified"])
            transition = graph.transition(item)
            event["transition"] = transition
            event["target_role"] = next_role
        graph_execution.append(event)
        if next_role is not None and event["transition"] != "ADVANCE":
            break
    generation1_log = list(graph.transition_log)

    # Reuse the same trained adapters in a fresh graph generation.
    graph2 = SkillGraph(nodes, generation=2)
    old_receipt = receipt("A", "B", 1, "effect-A-g1")
    stale_replay = graph2.transition(old_receipt)
    stale_replay_unchanged = graph2.state() == ("A", 2, (), ())
    assert stale_replay == "YIELD" and stale_replay_unchanged

    generation2_execution = []
    for role, _x, _y, next_role in sequence:
        decision, _chosen = graph2.dispatch(role, generation=2)
        if decision != "PROPOSE":
            generation2_execution.append({"role": role, "decision": decision})
            break
        event = {"role": role, "decision": decision}
        if next_role is not None:
            prior_rows = graph_rows.get(role)
            verified = bool(prior_rows) and (
                (base64.b64decode(prior_rows["packed_pairs_b64"])[0] >> 6) == ((base64.b64decode(prior_rows["packed_pairs_b64"])[0] >> 4) & 3))
            item = receipt(role, next_role, 2, "effect-" + role + "-g2",
                           verified=verified)
            transition = graph2.transition(item)
            event["transition"] = transition
            if transition != "ADVANCE":
                generation2_execution.append(event)
                break
        generation2_execution.append(event)
    generation2_log = list(graph2.transition_log)
    # Full-state serialization/readback for both role adapters; base immutability.
    snapshots = {}
    snapshot_exact = {}
    for role, model in (("B", adapter_b), ("C", adapter_c)):
        state = clone_state(model)
        buffer = io.BytesIO()
        torch.save(state, buffer)
        payload = buffer.getvalue()
        restored = torch.load(io.BytesIO(payload), map_location="cpu",
                              weights_only=True)
        model.load_state_dict(restored)
        snapshots[role] = {"sha256": hashlib.sha256(payload).hexdigest(),
                           "bytes": len(payload)}
        snapshot_exact[role] = exact_state(model, state)

    result = {
        "allocation": "needle-role-graph-3775-v1",
        "seed": SEED,
        "environment": {"platform": platform.platform(),
                        "python": platform.python_version(),
                        "torch": torch.__version__, "device": "cpu",
                        "threads": torch.get_num_threads(),
                        "deterministic": torch.are_deterministic_algorithms_enabled()},
        "frozen_design": {"base_rows": N_BASE, "support_rows_per_adapter": N_SUPPORT,
                          "heldout_rows_per_role": N_HELDOUT,
                          "base_steps": BASE_STEPS, "adapter_steps": ADAPTER_STEPS,
                          "graph_edges": [["A", "B"], ["B", "C"]],
                          "role_versions": {"A": version_of("A"),
                                            "B": version_of("B"),
                                            "C": version_of("C")}},
        "training_ms": {"base": base_train_ms, "adapter_B": b_train_ms,
                        "adapter_C": c_train_ms},
        "flat_dispatch": flat_rows,
        "graph_dispatch": graph_rows,
        "generation_1_execution": graph_execution,
        "generation_1_valid_transitions": generation1_log,
        "invalid_transition_controls": controls,
        "generation_2_old_receipt": {"decision": stale_replay,
                                     "state_unchanged": stale_replay_unchanged},
        "generation_2_execution": generation2_execution,
        "generation_2_valid_transitions": generation2_log,
        "generation_2_final_node": graph2.current,
        "adapter_snapshots": snapshots,
        "adapter_snapshot_exact": snapshot_exact,
        "base_immutable": exact_state(base, base_before),
        "scope": "synthetic fixture; graph effects are oracle test receipts, not real application effects or authority",
    }
    raw = json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    zipped = gzip.compress(raw, mtime=0)
    envelope = {"result_sha256": hashlib.sha256(raw).hexdigest(),
                "result_bytes": len(raw),
                "result_gzip_b64": base64.b64encode(zipped).decode()}
    print(json.dumps(envelope, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
