"""Emit a no-authority semantic probe from the exact frame before PNG publication."""
import sys
import time
from pathlib import Path

from PIL import ImageGrab

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from release_recovery_backend_v1 import Backend as Previous, suite
from session_v4 import Frame
from inkscape_selection_frame_probe_v1 import reconcile_artifact
from semantic_probe_runtime_v1 import SemanticProbeRegistry


class Backend(Previous):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.semantic_probes = SemanticProbeRegistry()

    def register_semantic_probe(self, identifier, plan):
        return self.semantic_probes.register(identifier, plan)

    def _probe(self, identifier, index, sequence, capture_ns, frame):
        return self.semantic_probes.probe(identifier, index, sequence, capture_ns, frame)

    def snapshot(self, identifier, index):
        before = self.binding(); start = time.perf_counter_ns()
        image = ImageGrab.grab(xdisplay=self.session.name).convert("RGB")
        capture = time.perf_counter_ns()
        source = Frame(image.width, image.height, image.mode, image.tobytes())
        context = self.session.context(); context_ns = time.perf_counter_ns()
        after = self.binding()
        self.observed_focus = after["focus"] if before["focus"] == after["focus"] else None
        self.observed_pointer = (dict(after) if before == after and
                                 after["surface"] is not None else None)
        packet = self.encoder.encode(source, action_id=f"{identifier}:{index}",
                                     observed_ns=capture, context=context)
        frame = self.decoder.accept(packet)
        if frame != source:
            raise AssertionError("wire reconstruction failed")
        self.sequence += 1
        sequence = self.sequence
        (self.out/f"{sequence:03d}.ait").write_bytes(packet)
        probe = self._probe(identifier, index, sequence, capture, frame)
        if probe is not None:
            self.emit(probe)
        artifact = self.images.publish(frame)
        reconciliation = None
        if probe is not None:
            reconciliation = reconcile_artifact(probe["score"], artifact["image"])
            self.emit({"event": "semantic_probe_reconciled", "id": identifier,
                       "step": index, "sequence": sequence,
                       "probe_completed_ns": probe["probe_completed_ns"],
                       "image": artifact["image"],
                       "image_ready_ns": artifact["image_ready_ns"],
                       "reconciliation": reconciliation,
                       "grants_input_authority": False})
        self.last_context = dict(context)
        self.emit({"event": "observation", "id": identifier, "step": index,
                   "sequence": sequence, "capture_ns": capture,
                   "context_ns": context_ns, "context": context, **artifact,
                   "input_focus_before": before["focus"],
                   "input_focus_after": after["focus"],
                   "focus_samples_match": before["focus"] == after["focus"],
                   "pointer_binding": self.observed_pointer,
                   "pointer_context_before": before,
                   "pointer_context_after": after,
                   "capture_ms": (capture-start)/1e6, "wire_bytes": len(packet),
                   "exact": True, "semantic_completion": "unknown",
                   "semantic_probe_sequence": sequence if probe is not None else None,
                   "semantic_probe_reconciliation": reconciliation})
