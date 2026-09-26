"""Small fixed-pool spatial heatmap grounder for Issue #4561."""
from __future__ import annotations

import torch
from torch import nn


class DeterministicAdaptiveAvgPool2d(nn.Module):
    """Separable fixed-matrix equivalent used by merged Issue #4482 evidence."""

    def __init__(self, input_size=(25, 40), output_size=(8, 10)):
        super().__init__()
        self.input_size = tuple(input_size)

        def matrix(source, target):
            weights = torch.zeros((target, source), dtype=torch.float32)
            for out_index in range(target):
                start = (out_index * source) // target
                end = ((out_index + 1) * source + target - 1) // target
                weights[out_index, start:end] = 1.0 / (end - start)
            return weights

        self.register_buffer("height_weights", matrix(input_size[0], output_size[0]))
        self.register_buffer("width_weights", matrix(input_size[1], output_size[1]))

    def forward(self, x):
        if tuple(x.shape[-2:]) != self.input_size:
            raise ValueError(f"expected feature map {self.input_size}, got {tuple(x.shape[-2:])}")
        return torch.einsum("oh,nchw,pw->ncop", self.height_weights, x, self.width_weights)


class TinyCoordinateGrounder(nn.Module):
    """Two spatial heatmaps: channel 0 is field, channel 1 is submit."""

    def __init__(self):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(1, 8, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(8, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.pool = DeterministicAdaptiveAvgPool2d((25, 40), (8, 10))
        self.heatmaps = nn.Conv2d(16, 2, kernel_size=1)

    def forward(self, x):
        return self.heatmaps(self.pool(self.stem(x)))


def batch_targets(labels, device):
    return torch.tensor([[r * 10 + c for r, c in (row["field_cell"], row["submit_cell"])]
                          for row in labels], dtype=torch.long, device=device)


def loss_for(logits, labels):
    if logits.ndim != 4 or tuple(logits.shape[1:]) != (2, 8, 10):
        raise ValueError(f"expected [N,2,8,10] heatmaps, got {tuple(logits.shape)}")
    targets = batch_targets(labels, logits.device)
    return sum(nn.functional.cross_entropy(logits[:, c].flatten(1), targets[:, c]) for c in range(2)) / 2
