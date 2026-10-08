"""Six frozen finite traces for Issue #5426 T2."""

RESOURCES = ("input_authority", "verifier_slot", "observation_slot")

SCENARIOS = [
    {
        "id": "safe_interleaving",
        "truthful": True,
        "claims": {"A": [1, 1, 0], "B": [0, 0, 1], "C": [0, 1, 0]},
        "actual": {"A": [1, 1, 0], "B": [0, 0, 1], "C": [0, 1, 0]},
        "events": [
            ["request", "A", 0], ["request", "B", 2], ["request", "C", 1],
            ["request", "A", 1], ["finish", "B"], ["finish", "C"], ["finish", "A"],
        ],
    },
    {
        "id": "truthful_cycle",
        "truthful": True,
        "claims": {"A": [1, 1, 0], "B": [1, 1, 0]},
        "actual": {"A": [1, 1, 0], "B": [1, 1, 0]},
        "events": [
            ["request", "A", 0], ["request", "B", 1], ["request", "A", 1],
            ["request", "B", 0], ["finish", "A"], ["finish", "B"],
        ],
    },
    {
        "id": "overestimated_claim",
        "truthful": False,
        "claims": {"A": [1, 1, 0], "B": [1, 1, 0]},
        "actual": {"A": [1, 0, 0], "B": [1, 1, 0]},
        "events": [
            ["request", "A", 0], ["request", "B", 1], ["request", "B", 0],
            ["finish", "A"], ["finish", "B"],
        ],
    },
    {
        "id": "underestimated_claim_expansion",
        "truthful": False,
        "claims": {"A": [1, 0, 0], "B": [1, 1, 0]},
        "actual": {"A": [1, 0, 0], "B": [1, 1, 0]},
        "events": [
            ["request", "A", 0], ["request", "B", 1],
            ["expand", "A", [1, 1, 0]], ["request", "A", 1], ["request", "B", 0],
            ["finish", "A"], ["finish", "B"],
        ],
    },
    {
        "id": "lease_expiry",
        "truthful": True,
        "claims": {"A": [1, 0, 0], "B": [1, 0, 0]},
        "actual": {"A": [1, 0, 0], "B": [1, 0, 0]},
        "events": [
            ["request", "A", 0], ["request", "B", 0], ["expire", "A"], ["finish", "B"],
        ],
    },
    {
        "id": "shared_fault_invalidation",
        "truthful": True,
        "claims": {"A": [1, 1, 0], "B": [0, 1, 1]},
        "actual": {"A": [1, 1, 0], "B": [0, 1, 1]},
        "events": [
            ["request", "A", 0], ["request", "A", 1], ["request", "B", 2],
            ["invalidate", 0], ["request", "B", 1], ["finish", "B"],
        ],
    },
]
