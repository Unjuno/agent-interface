from __future__ import annotations

import json

import numpy as np

from models import forward_logits, initialize, loss_and_gradients
from prepare import dataset


def main():
    (x, y), (bx, by), held = dataset(89100471)
    assert x.shape == (160, 1, 30, 40) and y.shape == (160,)
    assert (int(np.sum(y)), int(np.sum(1 - y))) == (80, 80)
    assert bx.shape == (80, 1, 30, 40) and (int(np.sum(by)), int(np.sum(1 - by))) == (40, 40)
    assert len(held) == 8 and all(a.shape == (80, 1, 30, 40) for a, _ in held.values())

    max_model = initialize(89100472, False)
    extent_model = initialize(89100472, True)
    assert np.array_equal(max_model[0], extent_model[0])
    assert np.array_equal(max_model[1], extent_model[1])
    assert np.array_equal(max_model[2], extent_model[2][:4])
    assert np.all(extent_model[2][4:] == 0)
    np.testing.assert_array_equal(forward_logits(x[:8], max_model, False), forward_logits(x[:8], extent_model, True))

    # Central finite-difference check all 49 scalar parameters; no optimizer updates.
    model = [np.array(v, dtype=np.float32, copy=True) for v in extent_model]
    loss, grads = loss_and_gradients(x[:8], y[:8], model, True)
    eps = 1e-3
    maximum_relative_error = 0.0
    checked = 0
    for parameter_index, parameter in enumerate(model):
        for index in np.ndindex(parameter.shape):
            original = float(parameter[index])
            parameter[index] = original + eps
            plus = loss_and_gradients(x[:8], y[:8], model, True)[0]
            parameter[index] = original - eps
            minus = loss_and_gradients(x[:8], y[:8], model, True)[0]
            parameter[index] = original
            numeric = (plus - minus) / (2 * eps)
            analytic = float(grads[parameter_index][index])
            relative = abs(numeric - analytic) / max(1e-6, abs(numeric) + abs(analytic))
            maximum_relative_error = max(maximum_relative_error, relative)
            checked += 1
    if maximum_relative_error > 3e-3:
        raise AssertionError(f"gradient relative error {maximum_relative_error}")
    print(json.dumps({"checks": {"train_rows": len(y), "base_rows": len(by), "held_centers": len(held),
                                  "parameter_derivatives": checked, "max_symmetric_relative_error": maximum_relative_error,
                                  "optimizer_updates": 0}, "pass": True}, sort_keys=True))


if __name__ == "__main__":
    main()

