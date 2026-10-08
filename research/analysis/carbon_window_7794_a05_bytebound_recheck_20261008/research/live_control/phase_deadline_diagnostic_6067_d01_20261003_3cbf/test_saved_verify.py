"""Effective controls do not assume the first observed wait included sleep."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import auditor
import saved_verify
import test_auditor

class SavedControlTests(unittest.TestCase):
    def test_already_late_first_wait_still_has_twelve_effective_controls(self):
        f=test_auditor.frame()
        f["wait"]["begin_ns"]=f["wait"]["return_ns"]
        f["wait"]["sleeps"]=[]
        auditor.frame_metrics(f,f["due_ns"])
        with patch.object(auditor,"stream",return_value=[f]):
            r=saved_verify.controls("unused",json.loads(Path("plan.json").read_text()))
        self.assertEqual(r["rejected"],12)
if __name__=="__main__": unittest.main()
