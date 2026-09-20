"""Construction-only controls for #3869; no training or formal allocation."""
import torch

import runner


def test_seed_and_shapes():
    assert runner.SEEDS == (3467, 3468, 3469)
    for cls in range(3):
        x = runner.shifted_class(cls, 32, 8000 + cls)
        assert x.shape == (32, 6)
        assert torch.isfinite(x).all()
        assert torch.all(runner.teacher(x) == cls)


def test_shift_is_near_threshold_and_in_envelope():
    x = runner.shifted_class(1, 2048, 8456)
    assert torch.all(x[:, 0].abs() >= .071)
    assert torch.all(x[:, 0].abs() <= .149)
    assert torch.all(x[:, 1].abs() <= .10)
    assert torch.all(x[:, 2:4].abs() <= .05)
    assert torch.all((x[:, 4] >= .80) & (x[:, 4] <= 1.0))
    assert torch.all(runner.teacher(x) == 1)
    for cls in (0, 2):
        seed = 8450 + cls
        assert torch.equal(runner.shifted_class(cls, 128, seed), runner.balanced_class(cls, 128, seed))


def test_external_gate_fails_closed_without_training():
    model = runner.Needle()
    good = torch.tensor([.2, .2, .01, .01, .9, 1.])
    bads = [
        (runner.META | {"epoch": 8}, good, "YIELD_METADATA"),
        (runner.META | {"scope": "other"}, good, "YIELD_METADATA"),
        ({"intent": "other", "scope": runner.META["scope"], "epoch": runner.META["epoch"]}, good, "YIELD_METADATA"),
        (runner.META, torch.tensor([1.3, 0., 0., 0., .9, 1.]), "YIELD_ENVELOPE"),
        (runner.META, torch.tensor([float("nan"), 0., 0., 0., .9, 1.]), "YIELD_NONFINITE"),
    ]
    for meta, x, expected in bads:
        proposal, reason = runner.proposal(meta, x, model)
        assert proposal is None and reason == expected
    assert len(list(model.parameters())) == 6


def test_boundary_suite_constructs_exact_count():
    rows = runner.boundary_rows()
    assert rows.shape == (1536, 6)
    model = runner.Needle()
    assert all(runner.proposal(runner.META, x, model) == (None, "YIELD_BOUNDARY") for x in rows)


if __name__ == "__main__":
    test_seed_and_shapes()
    test_shift_is_near_threshold_and_in_envelope()
    test_external_gate_fails_closed_without_training()
    test_boundary_suite_constructs_exact_count()
    print("construction-only checks passed: 4/4; no training/formal allocation")
