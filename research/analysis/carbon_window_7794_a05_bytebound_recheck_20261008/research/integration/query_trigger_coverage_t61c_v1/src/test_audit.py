import json
from pathlib import Path
import unittest
from audit import audit_document
from controls import variants

ROOT=Path(__file__).resolve().parent.parent/'records'/'construction'/'batch-5'

class AuditControls(unittest.TestCase):
    def test_original(self):
        doc=json.loads((ROOT/'RAW.json').read_text())
        self.assertEqual(audit_document(doc,ROOT)['errors'],[])


def case(index):
    def method(self):
        original=json.loads((ROOT/'RAW.json').read_text())
        self.assertEqual(audit_document(original,ROOT)['errors'],[])
        name,edited=variants(original)[index]
        self.assertNotEqual(json.dumps(edited,sort_keys=True),json.dumps(original,sort_keys=True),name)
        self.assertTrue(audit_document(edited,ROOT)['errors'],name)
    return method

for i,name in enumerate(('decision','cookie','rows','triggers','exit','missing','duplicate','effect')):
    setattr(AuditControls,'test_'+name,case(i))

if __name__=='__main__':unittest.main()
