"""Source-only regression: historical GTK allocations must not run on PR/push.

This intentionally checks three fixed workflow templates, not arbitrary YAML.
No workflow, Docker image, GUI, experiment runner or model is executed here.
"""
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {'gtk-bounded-allocation-2836.yml': ('name: GTK bounded allocation after startup repair #2836', 'b6fdf0bdf5811f68a200bcf71ac4f967297a4b2b4114c0189c5c6f0a2d422f11'), 'gtk-formal-allocation-2606-v1.yml': ('name: GTK bounded formal allocation #2606 v1', 'f0b038b8f3f0e71f6496a7c1334ea4a7cccb7481c63df68f8e8ae6fc4df1b229'), 'gtk-xlib-allocation-2851.yml': ('name: GTK Xlib-backed bounded allocation #2851', '988909a7c8bbd47f7693cd87ec62fb5dd2a158d9e7e855b90e855804a0be2a57')}


def validate(text, name):
    header, separator, jobs = text.partition('\njobs:\n')
    if not separator or name not in EXPECTED:
        return False
    name_line, body_hash = EXPECTED[name]
    expected = name_line + '\n\non:\n  workflow_dispatch:\n'
    return (header == expected
            and hashlib.sha256(jobs.encode('utf8')).hexdigest() == body_hash)


class ManualDispatchContract(unittest.TestCase):
    def sources(self):
        return {n: (ROOT / '.github/workflows' / n).read_text() for n in EXPECTED}

    def test_exact_manual_templates(self):
        for name, text in self.sources().items():
            with self.subTest(name=name):
                self.assertTrue(validate(text, name))

    def test_job_bodies_remain_frozen(self):
        for name, text in self.sources().items():
            body = text.partition('\njobs:\n')[2]
            self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), EXPECTED[name][1])

    def test_pull_request_is_rejected(self):
        for name, text in self.sources().items():
            self.assertFalse(validate(text.replace('workflow_dispatch:', 'pull_request:'), name))

    def test_push_is_rejected(self):
        for name, text in self.sources().items():
            self.assertFalse(validate(text.replace('workflow_dispatch:', 'push:'), name))

    def test_extra_trigger_is_rejected(self):
        for name, text in self.sources().items():
            self.assertFalse(validate(text.replace('  workflow_dispatch:', '  workflow_dispatch:\n  schedule:'), name))

    def test_job_mutation_is_not_hidden(self):
        for name, text in self.sources().items():
            self.assertFalse(validate(text.replace('timeout-minutes: 15', 'timeout-minutes: 16'), name))

    def test_missing_trigger_is_rejected(self):
        for name, text in self.sources().items():
            self.assertFalse(validate(text.replace('on:\n  workflow_dispatch:', 'on: {}'), name))

    def test_unknown_name_is_rejected(self):
        self.assertFalse(validate(next(iter(self.sources().values())), 'unknown.yml'))


if __name__ == '__main__':
    unittest.main()
