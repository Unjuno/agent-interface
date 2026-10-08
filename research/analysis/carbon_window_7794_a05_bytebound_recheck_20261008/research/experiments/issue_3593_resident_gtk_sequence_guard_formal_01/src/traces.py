TRACES = {
    "current_rising_edges": [
        {"kind": "obs", "id": "r1", "seq": 1, "gen": 1, "target": 1, "value": True},
        {"kind": "obs", "id": "f2", "seq": 2, "gen": 1, "target": 1, "value": False},
        {"kind": "obs", "id": "r3", "seq": 3, "gen": 1, "target": 1, "value": True},
    ],
    "delayed_replacement_rollback": [
        {"kind": "replace", "seq": 3, "gen": 2, "target": 2},
        {"kind": "replace", "seq": 2, "gen": 1, "target": 1},
        {"kind": "obs", "id": "old-after-rollback", "seq": 4, "gen": 1, "target": 1, "value": True},
    ],
    "valid_new_generation": [
        {"kind": "replace", "seq": 3, "gen": 2, "target": 2},
        {"kind": "obs", "id": "new-r4", "seq": 4, "gen": 2, "target": 2, "value": True},
    ],
    "duplicate_replacement": [
        {"kind": "replace", "seq": 3, "gen": 2, "target": 2},
        {"kind": "replace", "seq": 3, "gen": 3, "target": 3},
        {"kind": "obs", "id": "gen2-r4", "seq": 4, "gen": 2, "target": 2, "value": True},
    ],
    "delayed_old_observation": [
        {"kind": "replace", "seq": 3, "gen": 2, "target": 2},
        {"kind": "obs", "id": "old-seq2", "seq": 2, "gen": 1, "target": 1, "value": True},
        {"kind": "obs", "id": "new-r4", "seq": 4, "gen": 2, "target": 2, "value": True},
    ],
    "delayed_current_generation_observation": [
        {"kind": "replace", "seq": 3, "gen": 2, "target": 2},
        {"kind": "obs", "id": "old-seq-same-gen", "seq": 2, "gen": 2, "target": 2, "value": True},
    ],
    "delayed_same_generation_revoke": [
        {"kind": "replace", "seq": 1, "gen": 2, "target": 2},
        {"kind": "obs", "id": "new-r3", "seq": 3, "gen": 2, "target": 2, "value": True},
        {"kind": "revoke", "seq": 2, "gen": 2},
        {"kind": "obs", "id": "new-f4", "seq": 4, "gen": 2, "target": 2, "value": False},
        {"kind": "obs", "id": "new-r5", "seq": 5, "gen": 2, "target": 2, "value": True},
    ],
    "valid_revoke": [
        {"kind": "obs", "id": "old-r1", "seq": 1, "gen": 1, "target": 1, "value": True},
        {"kind": "revoke", "seq": 2, "gen": 1},
        {"kind": "obs", "id": "old-r3", "seq": 3, "gen": 1, "target": 1, "value": True},
    ],
    "newer_sequence_but_older_generation_replace": [
        {"kind": "replace", "seq": 3, "gen": 2, "target": 2},
        {"kind": "replace", "seq": 4, "gen": 1, "target": 1},
        {"kind": "obs", "id": "gen2-r5", "seq": 5, "gen": 2, "target": 2, "value": True},
    ],
}

COMPARATORS = {
    "duplicate_true": [
        {"kind": "obs", "id": "x1", "seq": 1, "value": True},
        {"kind": "obs", "id": "x2", "seq": 2, "value": True},
    ],
    "arrival_true_then_delayed_false": [
        {"kind": "obs", "id": "true3", "seq": 3, "value": True},
        {"kind": "obs", "id": "false2", "seq": 2, "value": False},
    ],
}
