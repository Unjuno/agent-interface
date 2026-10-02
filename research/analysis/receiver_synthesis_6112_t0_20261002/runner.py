"""One formal finite protocol run. Hidden oracle file is never opened here."""
import json
from pathlib import Path

from candidate import correction_fields, evaluate

ROOT = Path(__file__).resolve().parent
prompts = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))
submissions = json.loads((ROOT / "submissions.json").read_text(encoding="utf-8"))
prompt_by_id = {row["case_id"]: row["prompt"] for row in prompts["cases"]}
outcomes = []
for response in submissions["responses"]:
    prompt = prompt_by_id[response["case_id"]]
    outcomes.append({"response_id": response["response_id"],
                     "decision": evaluate(prompt, response),
                     "correction_fields": correction_fields(prompt, response)})
record = {"candidate_invocations": len(outcomes), "auditor_invocations": 0,
          "formal_retries": 0, "outcomes": outcomes,
          "human_participants": 0, "hidden_truth_opened_by_runner": False}
(ROOT / "FORMAL.json").write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, sort_keys=True, indent=2))
