# Retained A10 image against Calc cue

Offline OCR preflight, not a GUI-control allocation: one Tesseract full-image pass over the retained A10 post-action PNG referenced in `calc_guard_composition_v2_20261030` predecessor evidence `compiled_guard_perception_wslc_20261030_a10/raw/bridge/images/2e670e3c113f44c883d7b8a06cc935e8.png`. The pinned image and input digest are in conditions; host mount paths are placeholders. No actor or consumed G10/A10 allocation was replayed.

Tesseract detected 29, 31 and 899 at y=163, while the historical two-cell cue expects 731 and 864 in its fixed regions [20,180,125,200] and [20,200,125,220]. Its result is unknown. This is expected workload/geometry mismatch, not an OCR accuracy estimate or a general rejection of the cue. For 899, confidence 74.2 is also below that cue's 90 threshold. The G10 and A10 blank FODS input SHA-256 matches, but their tasks are distinct from the two-cell cue; task, ground truth, UI geometry and scorer must be fixed consistently before a live run.

The container exact-ID absence was checked; saved stderr, TSV, conditions and derived token extraction are retained. Model/token/latency and real GUI effects were not measured.
