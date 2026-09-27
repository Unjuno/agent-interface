"""One deliberately excluded package/model construction probe."""

import json
import time

import needle


TOOLS = [
    {
        "name": "SET_FIELD",
        "description": "Set a visible profile field.",
        "parameters": {
            "type": "object",
            "properties": {
                "scope_id": {"type": "string"},
                "generation": {"type": "integer"},
                "field": {"type": "string", "enum": ["display_name", "timezone"]},
                "value": {"type": "string"},
            },
            "required": ["scope_id", "generation", "field", "value"],
        },
    }
]


def main():
    import os

    weights = os.environ["CONSTRUCTION_MODEL_PATH"]
    agent = needle.Needle(
        tools=TOOLS,
        system="device: isolated construction fixture; network: disabled",
        weights=weights,
    )
    started = time.perf_counter_ns()
    response = agent.complete(
        "Construction-only prompt, excluded from all formal data: "
        "For workspace demo at generation 3, set display_name to Mica.",
        max_new_tokens=128,
    )
    print(json.dumps({
        "construction_only": True,
        "prompt_is_not_in_formal_cases": True,
        "decision_latency_ms": (time.perf_counter_ns() - started) / 1_000_000,
        "response": response,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
