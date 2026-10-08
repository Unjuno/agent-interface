import copy
import unittest

from .audit_raw import EXPECTED, check, mutations


def fixture():
    rows = []
    for name in EXPECTED:
        rows.append({"case_id": name, "broker_status": 1, "receipts": {}, "responses": {},
                     "fake_invocation_count": 0, "fake_invocation_log": [], "ipc_files": [],
                     "externally_timed_out": False})
    for name, code, rid in (("exit_0", 0, "exit-0"), ("exit_23", 23, "exit-23")):
        row = rows[EXPECTED.index(name)]
        row.update(broker_status=code, fake_invocation_count=1, fake_invocation_log=["invoked"],
                   receipts={rid: {"returncode": code, "authority_granted": False}},
                   responses={rid: "fake-response\n"})
    rows[2].update(receipts={"timeout": {"returncode": None, "stop_reason": "HOST_BROKER_SUBPROCESS_TIMEOUT", "authority_granted": False}}, responses={"timeout": ""}, fake_invocation_count=1)
    rows[3].update(receipts={"unavailable": {"error_class": "FileNotFoundError", "stop_reason": "HOST_BROKER_EXECUTABLE_UNAVAILABLE", "authority_granted": False}}, responses={"unavailable": ""})
    rows[4].update(receipts={"malformed": {"error_class": "InvalidInstructions", "stop_reason": "HOST_MODEL_INSTRUCTIONS_REJECTED", "authority_granted": False}}, responses={"malformed": ""})
    rows[5].update(broker_status=None, externally_timed_out=True)
    rows[6].update(broker_status=0, fake_invocation_count=1, fake_invocation_log=["invoked"], ipc_files=["a-first.broker.json", "a-first.request.json", "a-first.response.jsonl", "z-last.request.json"], receipts={"a-first": {"returncode": 0, "authority_granted": False}}, responses={"a-first": "fake-response\n"})
    return {"schema": "broker-fake-child-result-v1", "case_ids": list(EXPECTED), "rows": rows}


class RawAuditTest(unittest.TestCase):
    def test_expected_complete_result_passes(self):
        self.assertEqual(check(fixture()), [])

    def test_all_eight_copy_mutations_are_rejected(self):
        values = mutations(fixture())
        self.assertEqual(len(values), 8)
        self.assertTrue(all(check(value) for _, value in values))

    def test_duplicate_row_is_rejected(self):
        value = fixture()
        value["rows"][1] = copy.deepcopy(value["rows"][0])
        self.assertIn("row_order_or_count", check(value))


if __name__ == "__main__":
    unittest.main()
