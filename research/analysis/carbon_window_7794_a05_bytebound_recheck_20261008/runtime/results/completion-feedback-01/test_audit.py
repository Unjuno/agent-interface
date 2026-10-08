import copy
import unittest
from pathlib import Path
from audit import load, check


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.package=load(Path(__file__).parent)

    def test_original(self):
        self.assertEqual(check(self.package)['exact_submissions'],1)

    def test_mutations_rejected(self):
        mutations={
            'duplicate_submission':lambda p:p.__setitem__('case/session/submission-history.jsonl',p['case/session/submission-history.jsonl']*2),
            'wrong_value':lambda p:p.__setitem__('case/session/submission-history.jsonl',p['case/session/submission-history.jsonl'].replace(b'completion1001063',b'wrong')),
            'replayed_input':lambda p:p.__setitem__('host/request-6.json',p['host/request-5.json']),
            'changed_png':lambda p:p.__setitem__(next(k for k in p if '/images/' in k and k.endswith('.png')),b'bad png'),
            'changed_source':lambda p:p.__setitem__('case/caller.mjs',b'changed'),
            'missing_review':lambda p:p.pop('host/review-6.json'),
            'missing_finish':lambda p:p.pop('case/session/finish.json'),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                package=copy.deepcopy(self.package);mutate(package)
                with self.assertRaises((ValueError,KeyError)):
                    check(package)


if __name__=='__main__':unittest.main()
