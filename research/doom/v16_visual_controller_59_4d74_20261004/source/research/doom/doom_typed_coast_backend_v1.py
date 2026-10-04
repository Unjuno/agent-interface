"""DOOM backend that emits typed capture evidence before full artifact publication."""
import time

from PIL import ImageGrab

from coast_backend_v1 import Backend as Previous, suite
from doom_typed_observation_v1 import extract_typed_observation
from session_v4 import Frame


class Backend(Previous):
    def __init__(self, session, out, emit, signal_readers):
        super().__init__(session, out, emit)
        if set(signal_readers) != {"health", "ammo"}:
            raise ValueError("exact health/ammo reader pair required")
        self.signal_readers = dict(signal_readers)

    def snapshot(self, identifier, index):
        before = self.binding()
        started_ns = time.perf_counter_ns()
        image = ImageGrab.grab(xdisplay=self.session.name).convert("RGB")
        capture_ns = time.perf_counter_ns()
        source = Frame(image.width, image.height, image.mode, image.tobytes())
        context = self.session.context()
        context_ns = time.perf_counter_ns()
        after = self.binding()
        self.observed_focus = after["focus"] if before["focus"] == after["focus"] else None
        self.observed_pointer = (dict(after)
            if before == after and after["surface"] is not None else None)
        self.sequence += 1
        metadata = {"id": identifier, "step": index, "sequence": self.sequence,
                    "capture_ns": capture_ns,
                    "pointer_binding": self.observed_pointer}
        typed = extract_typed_observation(
            image, metadata, self.signal_readers)
        self.emit(typed)
        typed_emit_return_ns = time.perf_counter_ns()

        packet = self.encoder.encode(
            source, action_id=f"{identifier}:{index}",
            observed_ns=capture_ns, context=context)
        frame = self.decoder.accept(packet)
        if frame != source:
            raise AssertionError("wire reconstruction failed")
        (self.out / f"{self.sequence:03d}.ait").write_bytes(packet)
        artifact = self.images.publish(frame)
        artifact_ready_ns = time.perf_counter_ns()
        self.last_context = dict(context)
        self.emit({"event": "observation", "id": identifier, "step": index,
            "sequence": self.sequence, "capture_ns": capture_ns,
            "context_ns": context_ns, "context": context, **artifact,
            "input_focus_before": before["focus"], "input_focus_after": after["focus"],
            "focus_samples_match": before["focus"] == after["focus"],
            "pointer_binding": self.observed_pointer,
            "pointer_context_before": before, "pointer_context_after": after,
            "capture_ms": (capture_ns - started_ns) / 1e6,
            "wire_bytes": len(packet), "exact": True,
            "frame_rgb_sha256": typed["frame_rgb_sha256"],
            "typed_ready_ns": typed["typed_ready_ns"],
            "typed_emit_return_ns": typed_emit_return_ns,
            "artifact_ready_ns": artifact_ready_ns,
            "capture_to_artifact_ready_ms": (artifact_ready_ns - capture_ns) / 1e6,
            "semantic_completion": "unknown"})
