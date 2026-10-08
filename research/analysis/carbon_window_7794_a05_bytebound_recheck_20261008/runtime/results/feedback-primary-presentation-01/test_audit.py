import copy,json,unittest
from audit import ROOT,audit,validate
class AuditTests(unittest.TestCase):
    def test_retained_cases(self):self.assertEqual(len(audit()),2)
    def test_mutations(self):
        case=ROOT/'01-matched';reply=json.loads((case/'host/reply-3.json').read_text());original=json.loads(reply['result']['content'][0]['text'])
        report=json.loads((case/'calls'/original['call_id']/'report.json').read_text());events=[json.loads(s) for s in (case/'events.jsonl').read_text().splitlines()]
        for change in ['redirect','marker','source','release','title','authority','replay','save_count']:
            with self.subTest(change=change):
                m=copy.deepcopy(original);e=copy.deepcopy(events)
                if change=='redirect':m['observation_references']['/feedback/observation']='/image'
                elif change=='marker':m['feedback']['observation']={'observation_ref':'/image'}
                elif change=='source':m['source']['sequence']+=1
                elif change=='release':m['result']['execution']['releases'][0]['verified']=False
                elif change=='title':m['feedback']['after_title']='other'
                elif change=='authority':m['feedback']['authority_granted']=True
                elif change=='replay':m['replay_allowed']=True
                else:e.append({'event':'save','token':'t1001069'})
                with self.assertRaises(ValueError):validate(m,report,e,'matched')
if __name__=='__main__':unittest.main()
