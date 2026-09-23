import json
import os
from pathlib import Path

import numpy as np
import torch
from torch import nn


ROOT = Path(__file__).parent


def load(base, rows):
    xs, ys = [], []
    for row in rows:
        image = np.fromfile(base / row["frame"], dtype=np.uint8).reshape(240, 320, 4)
        xs.append(image[:, :, 0][::8, ::8].astype(np.float32) / 255)
        ys.append(row.get("label", 0))
    return torch.tensor(np.asarray(xs)[:, None]), torch.tensor(ys)


def main():
    old = ROOT / "shiftout"
    fresh = ROOT / "freshout"
    old_rows = json.loads((old / "manifest.json").read_text())["rows"]
    fresh_rows = json.loads((fresh / "manifest.json").read_text())["rows"]
    x_base, y_base = load(old, [r for r in old_rows if r["split"] == "train"])
    x_shift, y_shift = load(old, [r for r in old_rows if r["split"] == "shift"][:80])
    x_fresh, y_fresh = load(fresh, fresh_rows)
    train_x = torch.cat([x_base, x_shift, x_fresh[:80]])
    train_y = torch.cat([y_base, y_shift, y_fresh[:80]])
    test_x, test_y = x_fresh[80:], y_fresh[80:]

    torch.manual_seed(2417)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(2417)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    device = torch.device("cpu" if os.environ.get("X11_SWEEP_CPU") == "1" else
                          ("cuda" if torch.cuda.is_available() else "cpu"))

    model = nn.Sequential(
        nn.Conv2d(1, 4, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        nn.Conv2d(4, 8, 3, padding=1), nn.ReLU(),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(8, 2),
    ).to(device)
    train_x, train_y = train_x.to(device), train_y.to(device)
    test_x, test_y = test_x.to(device), test_y.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    for _ in range(140):
        optimizer.zero_grad()
        loss = nn.functional.cross_entropy(model(train_x), train_y)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        positive_probability = torch.softmax(model(test_x), 1)[:, 1]

    results = []
    targets = test_y.tolist()
    probabilities = positive_probability.tolist()
    for threshold in (0.50, 0.60, 0.70, 0.75, 0.80, 0.90):
        predicted_positive = [p >= 0.5 for p in probabilities]
        accepted = [pred and p >= threshold for pred, p in zip(predicted_positive, probabilities)]
        results.append({
            "threshold": threshold,
            "accuracy": sum(pred == bool(target) for pred, target in zip(predicted_positive, targets)) / len(targets),
            "predicted_positive": sum(predicted_positive),
            "accept": sum(accepted),
            "accepted_false": sum(a and target != 1 for a, target in zip(accepted, targets)),
            "yield": len(targets) - sum(accepted),
        })
    print(json.dumps({"seed": 2417, "device": str(device), "rows": len(targets), "results": results}, indent=2))


if __name__ == "__main__":
    main()
