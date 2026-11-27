"""Research-only lossless image gate. No GUI, hash, or task oracle dependency."""

from dataclasses import dataclass
from time import perf_counter_ns


@dataclass(frozen=True)
class Frame:
    width: int
    height: int
    mode: str
    pixels: bytes

    def __post_init__(self):
        channels = {"RGB": 3, "RGBA": 4, "L": 1}.get(self.mode)
        if channels is None or self.width <= 0 or self.height <= 0:
            raise ValueError("Unsupported frame geometry or mode")
        if not isinstance(self.pixels, bytes):
            raise TypeError("Frame storage must be immutable bytes")
        if len(self.pixels) != self.width * self.height * channels:
            raise ValueError("Frame storage length does not match geometry")


@dataclass(frozen=True)
class Update:
    stream: str
    sequence: int
    base_sequence: int
    frame: Frame | None
    observed_ns: int
    action_id: str
    context: tuple
    compare_ns: int


class ExactGate:
    """O1 suppresses only exact repeats of an acknowledged, reliable stream base.

    The in-process benchmark transport is ordered and reliable. An adapter with
    loss/reconnect must establish a new stream (full first frame), never assume
    that a previously sent image is still present at the receiver.
    """

    def __init__(self, strategy: str, stream: str):
        if strategy not in ("O0", "O1"):
            raise ValueError(strategy)
        self.strategy = strategy
        self.stream = stream
        self.sequence = 0
        self.base_sequence = 0
        self.previous = None

    def push(self, frame: Frame, *, observed_ns: int, action_id: str,
             context: tuple = ()) -> Update:
        compare_ns = 0
        same = False
        if self.strategy == "O1":
            start = perf_counter_ns()
            prior = self.previous
            same = (prior is not None and prior.width == frame.width
                    and prior.height == frame.height and prior.mode == frame.mode
                    and prior.pixels == frame.pixels)
            compare_ns = perf_counter_ns() - start
        self.sequence += 1
        if not same:
            self.previous = frame
            self.base_sequence = self.sequence
        return Update(self.stream, self.sequence, self.base_sequence,
                      None if same else frame, observed_ns, action_id,
                      context, compare_ns)


class Receiver:
    """Refuse a missing, stale, reordered, or cross-session image reference."""

    def __init__(self, stream: str):
        self.stream = stream
        self.sequence = 0
        self.base_sequence = 0
        self.frame = None

    def accept(self, update: Update) -> Frame:
        if update.stream != self.stream or update.sequence != self.sequence + 1:
            raise ValueError("Stream gap, reorder, or wrong session: resync required")
        if update.frame is None:
            if self.frame is None or update.base_sequence != self.base_sequence:
                raise ValueError("Missing image base: resync required")
        else:
            if update.base_sequence != update.sequence:
                raise ValueError("Invalid full-frame base")
            self.frame = update.frame
            self.base_sequence = update.base_sequence
        self.sequence = update.sequence
        return self.frame
