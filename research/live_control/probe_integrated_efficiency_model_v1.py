"""Parse the retained compiled model artifact through the shared comparison adapter."""

import json
from pathlib import Path

from integrated_efficiency_model_v1 import parse


HERE = Path(__file__).resolve().parent


def main():
    retained = HERE / "results" / "compiled-gui-interface-live-05" / "2-positive" / "grounding-model"
    result = parse(retained, "compiled")
    assert result["grounding"]["field_point"] == [180, 243]
    assert result["grounding"]["submit_point"] == [270, 243]
    assert result["requested_model"] == "gpt-5.6-luna"
    assert result["requested_effort"] == "low"
    assert result["usage"]["input_tokens"] == 9395
    print(json.dumps({"passed": True, "retained_call_id": result["call_id"],
                      "input_tokens": result["usage"]["input_tokens"]}, indent=2))


if __name__ == "__main__":
    main()
