"""Conservative visual revisit detector for the MAP01 game viewport."""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

VIEWPORT = (320, 162, 962, 610)
DESCRIPTOR_SIZE = (64, 45)
REVISIT_MAE_THRESHOLD = 0.065
MAX_HISTORY = 8
MIN_LAG = 2


def descriptor(path: Path) -> Image.Image:
    with Image.open(path) as frame:
        return frame.convert("L").crop(VIEWPORT).resize(DESCRIPTOR_SIZE)


def normalized_mae(left: Image.Image, right: Image.Image) -> float:
    return ImageStat.Stat(ImageChops.difference(left, right)).mean[0] / 255.0


def find_revisit(current: Image.Image, history: list[Image.Image],
                 threshold: float = REVISIT_MAE_THRESHOLD) -> dict | None:
    """Return the closest non-adjacent recent view when similarity is calibrated high."""
    current_index = len(history)
    start = max(0, current_index - MAX_HISTORY)
    candidates = []
    for prior_index in range(start, current_index - MIN_LAG + 1):
        candidates.append((normalized_mae(current, history[prior_index]), prior_index))
    if not candidates:
        return None
    mae, prior_index = min(candidates)
    if mae > threshold:
        return None
    return {
        "prior_iteration": prior_index,
        "lag": current_index - prior_index,
        "normalized_mae": mae,
        "threshold": threshold,
    }


def sustained_revisit(flags: list[bool], window: int = 5, minimum: int = 3) -> bool:
    """Require repeated revisit evidence before exposing a planner advisory."""
    return bool(flags and flags[-1] and sum(flags[-window:]) >= minimum)


def recovery_commands(attempt: int) -> list[dict]:
    """Escalate and alternate a bounded escape path for repeated visual clusters."""
    direction = "turn_left" if attempt % 2 == 0 else "turn_right"
    turns = 1 if attempt < 2 else 2
    commands = [{"action": "backward", "extent": "long"}]
    commands.extend({"action": direction, "extent": "long"} for _ in range(turns))
    if attempt >= 2:
        commands.append({"action": "use", "extent": "pulse"})
    commands.append({"action": "forward", "extent": "long"})
    return commands
