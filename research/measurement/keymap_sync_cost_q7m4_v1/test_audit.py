"""Effective raw-evidence controls: unchanged record passes before every mutation."""
import copy,hashlib,json,os
from pathlib import Path
import unittest
from audit import audit_block
HERE=Path(__file__).resolve().parent
class Controls(unittest.TestCase):
    def test_twelve_effective_mutations(self):
        root=Path(os.environ.get('EVIDENCE_BLOCK',str(HERE/'construction01'))); rows=[json.loads(x) for x in (root/'2-0.jsonl').read_text().splitlines()];receipt=json.loads((root/'2-0.process.json').read_text())
        def alter(field,value):return lambda a,b:a[3].__setitem__(field,value)
        mutations=[alter('index',True),alter('decision',False),alter('decision',0),alter('request_after',rows[3]['request_after']+1),alter('processed',0),alter('pre','00'*32),alter('after_ns',0),lambda a,b:a[3]['events'].pop(),lambda a,b:a.pop(),lambda a,b:b.__setitem__('returncode',23),lambda a,b:a[-1].__setitem__('final_keymap','01'*32),lambda a,b:a[3]['events'][0].__setitem__('synthetic',1)]
        for i,mutate in enumerate(mutations):
            with self.subTest(control=i):
                audit_block(rows,receipt,receipt['rep'],2,0,rows[0]['samples'])
                a,b=copy.deepcopy(rows),copy.deepcopy(receipt);old=json.dumps([a,b],sort_keys=True);mutate(a,b)
                self.assertNotEqual(old,json.dumps([a,b],sort_keys=True))
                with self.assertRaises(ValueError):audit_block(a,b,receipt['rep'],2,0,rows[0]['samples'])
if __name__=='__main__':unittest.main()
