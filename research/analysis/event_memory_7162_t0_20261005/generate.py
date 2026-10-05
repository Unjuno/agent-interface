"""Seed cue-matched intentions across lifecycle and provenance states."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
states = [
    ("pending", "PENDING", "CONFIRMED"),
    ("unknown_effect", "UNKNOWN_EFFECT", "CONFIRMED"),
    ("complete", "COMPLETE", "CONFIRMED"),
    ("cancelled", "CANCELLED", "CONFIRMED"),
    ("superseded", "SUPERSEDED", "CONFIRMED"),
    ("authority_revoked", "PENDING", "REVOKED"),
    ("unknown_origin", "PENDING", "UNKNOWN"),
]
data = {"schema": "cue-resumption-t0-v1", "cue": "upload-result",
        "intentions": [{"id": name, "cue": "upload-result", "lifecycle": lifecycle,
                        "authority": authority,
                        "text": f"When upload-result appears, check status ({lifecycle})"}
                       for name, lifecycle, authority in states]}
(HERE / "INPUT.json").write_text(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")
print(json.dumps({"intentions": len(states), "matching_cues": len(states),
                  "eligible": 2, "final_cue": data["cue"]}, sort_keys=True))
