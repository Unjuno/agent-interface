"""Raw-only mutation controls: no child or producer invocation."""
import copy
import json
from pathlib import Path
import unittest
from audit_v2 import audit

HERE = Path(__file__).resolve().parent
FOLDER = HERE / 'results/boundary-01'

def mutations(raw):
    out = {}
    d = copy.deepcopy(raw)
    d['rows'][0]['processes'][1]['started_utc'] = d['rows'][0]['processes'][0]['started_utc']
    out['reader-before-writer-exit'] = d
    d = copy.deepcopy(raw)
    d['rows'][0]['processes'][1]['argv'][2] = 'write'
    out['argv-mode-mismatch'] = d
    d = copy.deepcopy(raw)
    d['environment']['python'] = 'unrecorded interpreter'
    out['unfrozen-interpreter'] = d
    d = copy.deepcopy(raw)
    for key in ('recovery', 'second_recovery'):
        d['rows'][0][key]['reason'] = 'MANDATORY_COMPLETE'
    for p in d['rows'][0]['processes'][1:]:
        value = json.loads(p['stdout'])
        value['reason'] = 'MANDATORY_COMPLETE'
        p['stdout'] = json.dumps(value) + '\r\n'
    out['contradictory-complete-reason'] = d
    return out

class AuditV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((FOLDER / 'raw.json').read_bytes())

    def test_original_retained_record_accepts(self):
        result = audit(self.raw, FOLDER)
        self.assertEqual((result['complete'], result['counterexamples'], result['partial_unknown']), (3, 1, 5))

    def test_reader_cannot_precede_writer_exit(self):
        with self.assertRaises(ValueError):
            audit(mutations(self.raw)['reader-before-writer-exit'], FOLDER)

    def test_argv_must_agree_with_mode(self):
        with self.assertRaises(ValueError):
            audit(mutations(self.raw)['argv-mode-mismatch'], FOLDER)

    def test_interpreter_must_agree_with_freeze(self):
        with self.assertRaises(ValueError):
            audit(mutations(self.raw)['unfrozen-interpreter'], FOLDER)

    def test_complete_reason_cannot_join_partial_result(self):
        with self.assertRaises(ValueError):
            audit(mutations(self.raw)['contradictory-complete-reason'], FOLDER)

    def test_additional_join_and_type_controls(self):
        edits = [lambda d: d['environment'].update(platform='unrecorded'),
            lambda d: d['environment'].update(executable_sha256='0'*64),
            lambda d: d['rows'][0]['processes'][0]['argv'].__setitem__(4, '{}'),
            lambda d: d['rows'][1]['processes'][0].update(started_utc=d['rows'][0]['processes'][0]['started_utc']),
            lambda d: d['rows'][0]['processes'][0].update(exit_code=True),
            lambda d: d['rows'][0]['recovery'].update(extra='unobserved'),
            lambda d: d['rows'][0]['processes'][0].update(started_utc='bad-time'),
            lambda d: d['rows'][0].update(journal_sha256='0'*64),
            lambda d: d['rows'].pop(),
            lambda d: d['rows'].append(copy.deepcopy(d['rows'][0]))]
        for i, edit in enumerate(edits):
            with self.subTest(control=i):
                changed = copy.deepcopy(self.raw)
                edit(changed)
                with self.assertRaises(ValueError):
                    audit(changed, FOLDER)

if __name__ == '__main__':
    unittest.main()
