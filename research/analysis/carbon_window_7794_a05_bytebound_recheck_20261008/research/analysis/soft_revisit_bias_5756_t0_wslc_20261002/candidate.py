from fixtures import POLICIES
from policy import choose_edge


EVENT_BUDGET = 12


def run(fixtures):
    rows = []
    for fixture in fixtures:
        for policy_name in POLICIES:
            public = fixture["agent_view"]
            environment = fixture["environment"]
            memory = {}
            edge_visits = {edge["id"]: 0 for edge in public["edges"]}
            events = []
            observed_labels = []
            claimed_target = None
            event_index = 0

            while event_index < EVENT_BUDGET and claimed_target is None:
                events.append({"type": "observe", "node": "root", "source_epoch": public["source_epoch"]})
                event_index += 1
                edge_id = choose_edge(public, public["task"], memory, policy_name)
                if edge_id is None:
                    events.append({"type": "refuse", "reason": "no_safe_unvisited_edge"})
                    break
                edge = next(item for item in public["edges"] if item["id"] == edge_id)
                if not edge["reversible"]:
                    events.append({"type": "forbidden_traversal", "edge_id": edge_id})
                    break
                edge_visits[edge_id] += 1
                events.append({"type": "navigate", "edge_id": edge_id})
                event_index += 1
                visit = edge_visits[edge_id]

                label = None
                if edge_id == "alpha":
                    reveal = environment["reveal_profile_on_alpha_visit"]
                    if reveal is not None and visit >= reveal:
                        label = environment["alpha_observed_label"]
                elif edge_id == "beta":
                    label = "Help"

                if label is not None:
                    observed_labels.append(label)
                events.append({"type": "observe_child", "edge_id": edge_id, "label": label})
                event_index += 1
                if label == "Profile":
                    claimed_target = label
                    break

                memory[edge_id] = {
                    "visits": visit,
                    "last_epoch": public["source_epoch"],
                    "inspection_complete": environment["inspection_complete_after_visit"],
                }
                events.append({"type": "backtrack", "edge_id": edge_id})
                event_index += 1

            rows.append({
                "fixture_id": fixture["fixture_id"],
                "policy": policy_name,
                "events": events,
                "observed_labels": observed_labels,
                "claimed_target": claimed_target,
                "event_count": len(events),
                "budget": EVENT_BUDGET,
            })
    return rows
