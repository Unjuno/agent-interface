import copy,json,unittest
from pathlib import Path
from audit import ROOT,audit,validate
class AuditTests(unittest.TestCase):
    def test_retained_cases(self):self.assertEqual(len(audit()),3)
    def test_corruptions_are_rejected(self):
        original=json.loads((ROOT/'01-matched/replies/003.json').read_text())
        events=[json.loads(s) for s in (ROOT/'01-matched/events.jsonl').read_text().splitlines()]
        for change in ['verdict','receipt','release','image','title','authority','replay','duplicate_save']:
            with self.subTest(change=change):
                row=copy.deepcopy(original);ev=copy.deepcopy(events);m=row['metadata']
                if change=='verdict':m['feedback']['status']='pending'
                elif change=='receipt':m['result']['status']='failed'
                elif change=='release':m['result']['execution']['releases'][0]['keys_down']=['a']
                elif change=='image':row['image_sha256']='wrong'
                elif change=='title':m['feedback']['after_title']='different'
                elif change=='authority':m['feedback']['authority_granted']=True
                elif change=='replay':m['replay_allowed']=True
                else:ev.append({'event':'save'})
                with self.assertRaises(ValueError):validate(row,ev,'matched')
if __name__=='__main__':unittest.main()
