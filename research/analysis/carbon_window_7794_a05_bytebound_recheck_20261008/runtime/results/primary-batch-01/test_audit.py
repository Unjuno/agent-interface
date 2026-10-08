import copy,json,unittest
from pathlib import Path
from audit import load,check

def change(package, path, mutation):
    value=json.loads(package[path]);mutation(value);package[path]=json.dumps(value).encode()

def change_meta(package, number, mutation):
    def edit(reply):
        text=next(c for c in reply['result']['content'] if c['type']=='text')
        value=json.loads(text['text']);mutation(value);text['text']=json.dumps(value)
    change(package,f'host/reply-{number}.json',edit)

class AuditTest(unittest.TestCase):
    def test_original_and_negative_controls(self):
        original=load(Path(__file__).parent)
        self.assertEqual(check(original)['exact_submissions'],1)
        mutations={
            'duplicate_submission':lambda p:p.__setitem__('case/session/submission-history.jsonl',p['case/session/submission-history.jsonl']*2),
            'wrong_value':lambda p:p.__setitem__('case/session/submission-history.jsonl',p['case/session/submission-history.jsonl'].replace(b'completion1001064',b'wrong')),
            'missing_alias':lambda p:change_meta(p,2,lambda m:m['minted'].pop()),
            'wrong_source':lambda p:change_meta(p,2,lambda m:m.__setitem__('source_sequence',99)),
            'old_click_source':lambda p:change(p,'host/request-5.json',lambda r:r['arguments'].__setitem__('source_sequence',1)),
            'replayed_input':lambda p:p.__setitem__('host/request-7.json',p['host/request-6.json']),
            'changed_primary':lambda p:p.__setitem__('case/host-bundle/primary_caller.mjs',b'changed'),
            'missing_review':lambda p:p.pop('host/review-7.json'),
        }
        for name,mutate in mutations.items():
            with self.subTest(name=name):
                package=copy.deepcopy(original);mutate(package)
                with self.assertRaises((ValueError,KeyError)):check(package)

if __name__=='__main__':unittest.main()
