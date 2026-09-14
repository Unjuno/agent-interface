"""Engineering-only full mechanics test for all three comparison arms."""

import json
from pathlib import Path

from integrated_efficiency_client_v1 import RuntimeClient


HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "integrated-efficiency-three-arm-mechanics-02"
SEED = 991027
POINTS = {"A": {"field_point": [226, 401], "submit_point": [376, 401]},
          "B": {"field_point": [650, 558], "submit_point": [688, 634]}}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    reports = {}
    for arm in ("plain", "ephemeral", "persistent"):
        with RuntimeClient(OUT / arm, SEED) as client:
            aliases = None
            invalidation = None
            for index, task in enumerate(client.ready["goal"]["tasks"]):
                source = client.navigate(task)
                grounding = POINTS[task["layout"]]
                if arm == "plain":
                    result = client.execute_plain(task, grounding)
                elif arm == "ephemeral":
                    aliases, refusal = client.mint(task["layout"], source, grounding,
                                                    f"{task['task_id']}_{task['layout'].lower()}")
                    assert refusal is None
                    result = client.execute_handles(task, aliases)
                else:
                    if index == 0:
                        aliases, refusal = client.mint("A", source, grounding, "persistent_a")
                        assert refusal is None
                    elif index == 3:
                        old, old_program = client.check(aliases["field"], [12, 19],
                                                        "old-field-invalidation")
                        invalidation = {"status": old["status"], "eligible": old["eligible"],
                                        "pointer_admissions": len(old_program["pointer_admissions"])}
                        assert invalidation == {"status": "MISSING", "eligible": False,
                                                "pointer_admissions": 0}
                        aliases, refusal = client.mint("B", source, grounding, "persistent_b")
                        assert refusal is None
                    result = client.execute_handles(task, aliases)
                assert result["status"] == "completed"
            evaluation = client.finish("finish-three-arm-" + arm)
            assert evaluation["success"] is True
            mints = sum(len(row["point_mints"]) for row in client.programs)
            button_down = sum(event["operation"] == "button_down"
                              for row in client.programs for event in row["pointer_admissions"])
            assert mints == {"plain": 0, "ephemeral": 12, "persistent": 4}[arm]
            assert button_down == 12
            reports[arm] = {"tasks": 6, "mints": mints, "button_down": button_down,
                            "programs": len(client.programs), "durable_calls": client.durable_calls,
                            "invalidation": invalidation, "evaluation": evaluation}
    report = {"schema": "integrated_efficiency_three_arm_mechanics_v1",
              "passed": True, "seed": SEED, "human_inspected_points": POINTS,
              "model_calls": 0, "arms": reports,
              "claim": "engineering mechanics only; excluded from formal comparison"}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps({"passed": True, "arms": {key: {k: row[k] for k in
          ("tasks", "mints", "button_down", "programs", "durable_calls")}
          for key, row in reports.items()}}, indent=2))


if __name__ == "__main__":
    main()
