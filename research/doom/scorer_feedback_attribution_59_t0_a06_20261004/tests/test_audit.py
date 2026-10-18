from __future__ import annotations
import copy,json,os,unittest
from pathlib import Path
from audit_a05_raw import audit_document
def load_document():
    return json.loads(Path(os.environ.get("A06_RAW_INPUT","/input/a05-candidate.raw.json")).read_text(encoding="utf-8"))
class StrictRawAuditTests(unittest.TestCase):
    def test_exact_retained_candidate_bytes_pass(self):
        audit_document(load_document())
    def assert_mutation_rejected(self,mutate):
        document=copy.deepcopy(load_document()); mutate(document)
        with self.assertRaisesRegex(ValueError,"exact preregistered five-case contract"): audit_document(document)
    def test_duplicate_case_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"].__setitem__(2,copy.deepcopy(d["cases"][0])))
    def test_omitted_case_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"].pop())
    def test_relabelled_case_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"][0].__setitem__("case","02-MAP_EXIT"))
    def test_label_payload_kind_mismatch_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"][0]["event"].__setitem__("kind","MAP_EXIT"))
    def test_polarity_change_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"][0]["event"].__setitem__("polarity","negative"))
    def test_useful_flag_change_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"][0]["event"].__setitem__("useful",False))
    def test_unexpected_extra_case_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"].append(copy.deepcopy(d["cases"][0])))
    def test_changed_a05_disposition_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"][2]["a05"].__setitem__("accepted",True))
    def test_json_bool_to_integer_type_confusion_rejected(self):
        self.assert_mutation_rejected(lambda d:d["cases"][0]["event"].__setitem__("useful",1))
if __name__=="__main__": unittest.main(verbosity=2)
