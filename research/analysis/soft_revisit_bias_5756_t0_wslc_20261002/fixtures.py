import copy


POLICIES = ("stateless", "hard", "soft", "exhaustive")


def build_fixtures():
    specs = []
    for kind, count, reveal in (
        ("stable", 8, 1),
        ("partial", 8, 2),
        ("revision", 8, 2),
        ("no_target", 4, None),
        ("unsafe", 4, None),
    ):
        for i in range(count):
            fixture_id = f"{kind}-{i:02d}"
            specs.append({
                "fixture_id": fixture_id,
                "agent_view": {
                    "source_epoch": 1,
                    "task": "open profile",
                    "edges": [
                        {
                            "id": "alpha",
                            "label": "Profile",
                            "nearby": "recently changed" if kind == "revision" else "",
                            "saliency": 90,
                            "reversible": kind != "unsafe",
                            "revision_hint": kind == "revision",
                            "display_order": 0,
                        },
                        {
                            "id": "beta",
                            "label": "Help",
                            "nearby": "",
                            "saliency": 10,
                            "reversible": True,
                            "revision_hint": False,
                            "display_order": 1,
                        },
                    ],
                },
                "environment": {
                    "kind": kind,
                    "reveal_profile_on_alpha_visit": reveal,
                    "alpha_observed_label": "Settings" if kind == "no_target" and i % 2 == 0 else "Profile",
                    "inspection_complete_after_visit": kind in ("stable", "no_target", "unsafe"),
                    "epoch": 1,
                },
                "oracle": {
                    "target_label": "Profile" if kind in ("stable", "partial", "revision") else None,
                    "target_edge": "alpha" if kind in ("stable", "partial", "revision") else None,
                    "forbidden_edges": ["alpha"] if kind == "unsafe" else [],
                },
            })
    assert len(specs) == 32
    return specs


def public_fixtures(fixtures):
    return copy.deepcopy([{k: v for k, v in f.items() if k != "oracle"} for f in fixtures])
