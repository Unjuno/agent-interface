import unittest
try:
    from verify_packet import corruptions,row_errors,manifest_errors
except ImportError:
    corruptions=row_errors=manifest_errors=None
from test_packet_a11 import packet
from pathlib import Path
import tempfile
import json

class RetainedTests(unittest.TestCase):
    def test_saved_row_controls_include_post_admission_custody(self):
        self.assertIsNotNone(corruptions,'A11 retained verifier missing')
        with tempfile.TemporaryDirectory() as temp:
            path,data,source,raw=packet(Path(temp))
            self.assertEqual(row_errors(data,raw['rows'][0],raw['fixture'],0,raw['freeze_sha256']),[])
            result=corruptions(raw,data,raw['fixture'],raw['freeze_sha256'])
            self.assertGreaterEqual(len(result),25)
            self.assertTrue(all(result.values()),result)
            self.assertTrue(result['missing_drift_poll'])
            self.assertTrue(result['early_dispatch'])
            self.assertTrue(result['refused_save'])

if __name__=='__main__':unittest.main()
