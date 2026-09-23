import json
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


def build(device):
    torch.manual_seed(2417)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(2417)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    return nn.Sequential(
        nn.Conv2d(1, 4, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        nn.Conv2d(4, 8, 3, padding=1), nn.ReLU(),
        nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(8, 2),
    ).to(device)


def train(device, x, y):
    model = build(device)
    x, y = x.to(device), y.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=0.01)
    for _ in range(140):
        opt.zero_grad()
        loss = nn.functional.cross_entropy(model(x), y)
        loss.backward()
        opt.step()
    return model


def main():
    old = ROOT / "shiftout"
    fresh = ROOT / "freshout"
    old_rows = json.loads((old / "manifest.json").read_text())["rows"]
    fresh_rows = json.loads((fresh / "manifest.json").read_text())["rows"]
    xb, yb = load(old, [r for r in old_rows if r["split"] == "train"])
    xs, ys = load(old, [r for r in old_rows if r["split"] == "shift"][:80])
    xf, yf = load(fresh, fresh_rows)
    train_x = torch.cat([xb, xs, xf[:80]])
    train_y = torch.cat([yb, ys, yf[:80]])
    test_x, test_y = xf[80:], yf[80:]

    cpu = train(torch.device("cpu"), train_x, train_y)
    result = {"rows": len(test_y), "seed": 2417, "cuda_available": torch.cuda.is_available()}
    with torch.no_grad():
        cpu_prob = torch.softmax(cpu(test_x), 1)[:, 1].numpy()
    result["cpu"] = {
        "accuracy": float(((cpu_prob >= 0.5) == test_y.numpy()).mean()),
        "positive": int((cpu_prob >= 0.5).sum()),
        "p60": int((cpu_prob >= 0.6).sum()),
        "p75": int((cpu_prob >= 0.75).sum()),
        "min_positive": float(cpu_prob[cpu_prob >= 0.5].min()),
        "max_negative": float(cpu_prob[cpu_prob < 0.5].max()),
    }
    if torch.cuda.is_available():
        cuda = train(torch.device("cuda"), train_x, train_y)
        with torch.no_grad():
            cuda_prob = torch.softmax(cuda(test_x.cuda()), 1)[:, 1].cpu().numpy()
        result["cuda"] = {
            "accuracy": float(((cuda_prob >= 0.5) == test_y.numpy()).mean()),
            "positive": int((cuda_prob >= 0.5).sum()),
            "p60": int((cuda_prob >= 0.6).sum()),
            "p75": int((cuda_prob >= 0.75).sum()),
            "min_positive": float(cuda_prob[cuda_prob >= 0.5].min()),
            "max_negative": float(cuda_prob[cuda_prob < 0.5].max()),
            "mean_abs_prob_delta": float(np.abs(cpu_prob - cuda_prob).mean()),
            "same_classification": bool(np.array_equal(cpu_prob >= 0.5, cuda_prob >= 0.5)),
        }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
