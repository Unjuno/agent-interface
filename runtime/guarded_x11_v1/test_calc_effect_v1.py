"""The public Calc effect gate must reject forged filesystem custody."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.calc_effect_v1 import (
    ARTIFACT_NAME, CUSTODY_NAME, verify_call_owned_calc_effect)


FODS = (b'<?xml version="1.0"?><office:document-content '
    b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    b'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    b'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
    b'<office:body><office:spreadsheet><table:table table:name="Sheet1">'
    b'<table:table-row><table:table-cell office:value-type="float" office:value="731"/>'
    b'<table:table-cell office:value-type="float" office:value="864"/></table:table-row>'
    b'</table:table></office:spreadsheet></office:body></office:document-content>')
CALL_ID = '1' * 32
ATTEMPT_ID = 'synthetic-attempt'
CLOSE = {'status':'closed','verified':True,'owner_process_retired':True,
         'release_confirmed':True}


class CalcEffectGateTests(unittest.TestCase):
    def test_self_consistent_forged_sidecar_cannot_promote_parsed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / ARTIFACT_NAME
            artifact.write_bytes(FODS)
            info = artifact.stat()
            identity = [info.st_dev, info.st_ino, info.st_size,
                        info.st_mtime_ns, info.st_ctime_ns]
            close_hash = hashlib.sha256(json.dumps(CLOSE, sort_keys=True,
                separators=(',', ':')).encode()).hexdigest()
            custody = {
                'schema':'agent-interface/calc-artifact-custody-v1',
                'call_id':CALL_ID,'attempt_id':ATTEMPT_ID,
                'profile_id':'calc-ocr-save-v1','artifact_name':ARTIFACT_NAME,
                'artifact_sha256':hashlib.sha256(FODS).hexdigest(),
                'artifact_bytes':len(FODS),'artifact_identity':identity,
                'blank_sha256':'0'*64,'save_request_id':'caller-forged-save-id',
                'close_receipt_sha256':close_hash}
            (root / CUSTODY_NAME).write_text(json.dumps(custody), encoding='utf-8')

            result = verify_call_owned_calc_effect(root, call_id=CALL_ID,
                attempt_id=ATTEMPT_ID, close_receipt=CLOSE)

            self.assertEqual(result['status'], 'unknown', result)
            self.assertIsNone(result['task_success'], result)
            self.assertEqual(result['reason'],
                             'trusted_save_controller_unavailable', result)

    def test_missing_custody_stays_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            result = verify_call_owned_calc_effect(directory, call_id=CALL_ID,
                attempt_id=ATTEMPT_ID, close_receipt=CLOSE)
        self.assertEqual(result['status'], 'unknown', result)
        self.assertIsNone(result['task_success'], result)
        self.assertEqual(result['reason'], 'artifact_custody_unavailable', result)


if __name__ == '__main__':
    unittest.main()
