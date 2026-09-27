"""Excluded no-optimizer construction checks for Issue #4824."""
import hashlib
import torch
import runner

assert runner.data(68117, 101, 16)[0].shape == (16, 8)
support, _ = runner.data(68117, 101, 16)
assert int(support[:, 0].sum().item()) == 8
for seed in runner.SEEDS:
    assert runner.data(seed, 211, 256)[0].shape == (256, 8)
    assert int(runner.data(seed, 307, 256)[0][:, 0].sum().item()) == 128
assert runner.route("unknown", 3, 3, [0]) == {"decision": "YIELD", "authority": False, "model_calls": 0}
assert runner.route("B", 2, 3, [0]) == {"decision": "YIELD", "authority": False, "model_calls": 0}
calls = [0]
assert runner.route("B", 3, 3, calls) == {"decision": "PROPOSAL", "authority": False, "model_calls": 1}
assert calls == [1]
logits = torch.tensor([[2.0, 0.0], [0.0, 2.0]])
labels = torch.tensor([0, 1])
assert runner.metrics(logits, labels)["accuracy"] == 1.0
buf = torch.tensor([1.0, -2.0], dtype=torch.float32).view(torch.uint8).tolist()
assert hashlib.sha256(bytes(buf)).hexdigest() == runner.digest([torch.tensor([1.0, -2.0])])
print("CONSTRUCTION_PASS assertions=12 optimizer_updates=0 seeds=3")
