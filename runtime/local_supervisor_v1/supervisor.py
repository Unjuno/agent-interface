"""Bounded optional CONTINUE/YIELD supervisor; never an input authority."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

try:
    import torch
    from torch import nn
except ImportError:  # standard-library import remains useful for contract tests
    torch = None
    nn = None


FEATURES = 8
CONTINUE = "CONTINUE"
YIELD = "YIELD"


@dataclass(frozen=True)
class Decision:
    action: str
    confidence: float
    authority_granted: bool = False


if nn is not None:
    class SupervisorNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.layers = nn.Sequential(nn.Linear(FEATURES, 16), nn.Tanh(),
                                        nn.Linear(16, 2))

        def forward(self, x):
            return self.layers(x)
else:
    SupervisorNet = None


class LocalSupervisor:
    def __init__(self, model, *, threshold: float = 0.80, device: str = "cpu"):
        if torch is None or SupervisorNet is None:
            raise RuntimeError("torch is required for LocalSupervisor")
        if not 0.5 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0.5, 1.0]")
        self.model = model.to(device).eval()
        self.threshold = threshold
        self.device = device

    @torch.inference_mode()
    def decide(self, features: Sequence[float]) -> Decision:
        if len(features) != FEATURES:
            raise ValueError(f"expected {FEATURES} typed features")
        x = torch.tensor([list(features)], dtype=torch.float32, device=self.device)
        probabilities = torch.softmax(self.model(x), dim=-1)[0]
        index = int(probabilities.argmax().item())
        confidence = float(probabilities[index].item())
        action = CONTINUE if index == 0 and confidence >= self.threshold else YIELD
        return Decision(action=action, confidence=confidence)


def build(device: str = "cpu", seed: int = 0) -> LocalSupervisor:
    if torch is None or SupervisorNet is None:
        raise RuntimeError("torch is required for LocalSupervisor")
    torch.manual_seed(seed)
    return LocalSupervisor(SupervisorNet(), device=device)
