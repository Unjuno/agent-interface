import json
import unittest
from pathlib import Path

from candidate import correction_fields, evaluate

ROOT = Path(__file__).resolve().parent
PROMPTS = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))
SUBMISSIONS = json.loads((ROOT / "submissions.json").read_text(encoding="utf-8"))
PROMPT_BY_ID = {item["case_id"]: item["prompt"] for item in PROMPTS["cases"]}


class ProtocolConstructionTests(unittest.TestCase):
    def test_missing_contradictory_and_unsafe_synthesis_holds(self):
        for item in SUBMISSIONS["responses"]:
            outcome = evaluate(PROMPT_BY_ID[item["case_id"]], item)
            if item["response_id"] in {
                "missing_delivery_state", "contradictory_false_complete",
                "unsupported_authority_claim", "blind_replay",
                "packet_copy_without_application", "unsafe_stale_target_retry",
            }:
                self.assertTrue(outcome.startswith("HOLD_"), item["response_id"])

    def test_valid_synthesis_only_enters_separate_review(self):
        for rid in ("correct_uncertain_delivery", "correct_partial_edit"):
            item = next(x for x in SUBMISSIONS["responses"] if x["response_id"] == rid)
            self.assertEqual("READY_FOR_SEPARATE_ACTIVATION_REVIEW",
                             evaluate(PROMPT_BY_ID[item["case_id"]], item))

    def test_emergency_release_bypasses_missing_readback(self):
        item = next(x for x in SUBMISSIONS["responses"]
                    if x["response_id"] == "emergency_no_readback")
        self.assertEqual("SAFE_STOP_RELEASE_BYPASS",
                         evaluate(PROMPT_BY_ID[item["case_id"]], item))

    def test_correction_names_fields_without_echoing_answers(self):
        item = next(x for x in SUBMISSIONS["responses"]
                    if x["response_id"] == "unsupported_authority_claim")
        prompt = PROMPT_BY_ID[item["case_id"]]
        self.assertEqual(["authority_state"], correction_fields(prompt, item))
        emergency = next(x for x in SUBMISSIONS["responses"]
                         if x["response_id"] == "emergency_no_readback")
        self.assertEqual([], correction_fields(PROMPT_BY_ID[emergency["case_id"]], emergency))


if __name__ == "__main__":
    unittest.main()
