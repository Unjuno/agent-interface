import copy
import json
import unittest
from pathlib import Path
from skill_package import ActiveSkill, propose, validate_package

ROOT=Path(__file__).parent
PACKAGE=json.loads((ROOT/"package.json").read_text())
CASES=json.loads((ROOT/"cases.json").read_text())["cases"]

class SkillPackageTests(unittest.TestCase):
    def test_package_contract(self): self.assertEqual(validate_package(PACKAGE),[])
    def test_ten_frozen_cases(self):
        for case in CASES:
            with self.subTest(case=case["id"]):
                self.assertEqual(propose(PACKAGE,case["request"],case["state"],case["authority"]),case["expected"])
    def test_staged_field_continues_to_save(self):
        c=copy.deepcopy(next(x for x in CASES if x["id"]=="multistep_set_field"))
        c["state"]["staged"]={"digest_frequency":"weekly"}
        self.assertEqual(propose(PACKAGE,c["request"],c["state"],c["authority"]),{"name":"CLICK","arguments":{"scope_id":"workspace-7","generation":12,"target":"save_settings"}})
    def test_evidence_freshness_and_identity_fail_closed(self):
        c=copy.deepcopy(CASES[0]); c["state"]["freshness"]="stale"
        self.assertEqual(propose(PACKAGE,c["request"],c["state"],c["authority"]),{"name":"YIELD","arguments":{"reason":"missing_evidence"}})
        c=copy.deepcopy(CASES[0]); c["request"]["intent_version"]="settings-v0"
        self.assertEqual(propose(PACKAGE,c["request"],c["state"],c["authority"]),{"name":"YIELD","arguments":{"reason":"stale_scope"}})
    def test_invalid_package_rejected_without_active_mutation(self):
        store=ActiveSkill(PACKAGE); original=store.active_bytes
        bad=copy.deepcopy(PACKAGE); bad["allowed_actions"].append("DELETE")
        self.assertFalse(store.install(bad)); self.assertEqual(store.active_bytes,original)
    def test_valid_switch_then_exact_rollback(self):
        store=ActiveSkill(PACKAGE); original=store.active_bytes
        next_version=copy.deepcopy(PACKAGE); next_version["intent_version"]="settings-v2"
        self.assertTrue(store.install(next_version)); self.assertNotEqual(store.active_bytes,original)
        self.assertTrue(store.rollback()); self.assertEqual(store.active_bytes,original)
    def test_failed_replacement_version_does_not_expand_authority(self):
        c=copy.deepcopy(CASES[0]); c["authority"]["allowed_actions"]=["SET_FIELD","YIELD"]
        decision=propose(PACKAGE,c["request"],c["state"],c["authority"])
        self.assertEqual(decision,{"name":"YIELD","arguments":{"reason":"unsupported"}})
    def test_no_input_proposal_mutates_state(self):
        c=copy.deepcopy(CASES[0]); before=copy.deepcopy(c["state"])
        propose(PACKAGE,c["request"],c["state"],c["authority"])
        self.assertEqual(c["state"],before)

if __name__=="__main__": unittest.main(verbosity=2)

