"""The public Calc effect gate must reject forged filesystem custody."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime.guarded_x11_v1.calc_effect_v1 import (
    ARTIFACT_NAME, CUSTODY_NAME, _identity, _read_regular,
    _same_stat_version,
    verify_call_owned_calc_effect)


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
    def test_regular_artifact_read_uses_path_and_descriptor_stable_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / ARTIFACT_NAME
            artifact.write_bytes(b'blank')
            artifact.write_bytes(FODS)

            data, identity = _read_regular(artifact, max_bytes=64 * 1024)

            self.assertEqual(data, FODS)
            self.assertEqual(identity, _identity(artifact.lstat()))

    def test_same_descriptor_ctime_change_is_not_hidden_by_birthtime(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / ARTIFACT_NAME
            artifact.write_bytes(FODS)
            info = artifact.lstat()
            fields = {name: getattr(info, name) for name in (
                'st_mode', 'st_dev', 'st_ino', 'st_size', 'st_mtime_ns',
                'st_ctime_ns')}
            birthtime_ns = getattr(info, 'st_birthtime_ns', None)
            fields['st_birthtime_ns'] = (birthtime_ns if type(birthtime_ns) is int
                                         else info.st_ctime_ns)
            opened = SimpleNamespace(**fields)
            changed_fields = dict(fields)
            changed_fields['st_ctime_ns'] += 1
            changed = SimpleNamespace(**changed_fields)

            with patch('runtime.guarded_x11_v1.calc_effect_v1.os.fstat',
                       side_effect=(opened, changed)):
                with self.assertRaisesRegex(ValueError, 'file changed while reading'):
                    _read_regular(artifact, max_bytes=64 * 1024)

        self.assertEqual(_identity(opened), _identity(changed))
        self.assertFalse(_same_stat_version(opened, changed))

    def test_same_path_ctime_change_is_not_hidden_by_birthtime(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / ARTIFACT_NAME
            artifact.write_bytes(FODS)
            info = artifact.lstat()
            fields = {name: getattr(info, name) for name in (
                'st_mode', 'st_dev', 'st_ino', 'st_size', 'st_mtime_ns',
                'st_ctime_ns')}
            birthtime_ns = getattr(info, 'st_birthtime_ns', None)
            fields['st_birthtime_ns'] = (birthtime_ns if type(birthtime_ns) is int
                                         else info.st_ctime_ns)
            descriptor = SimpleNamespace(**fields)
            changed_fields = dict(fields)
            changed_fields['st_ctime_ns'] += 1
            path_after = SimpleNamespace(**changed_fields)

            with patch('runtime.guarded_x11_v1.calc_effect_v1.os.fstat',
                       side_effect=(descriptor, descriptor)), patch.object(
                           Path, 'lstat', side_effect=(info, path_after)):
                with self.assertRaisesRegex(ValueError, 'file changed while reading'):
                    _read_regular(artifact, max_bytes=64 * 1024)

        self.assertFalse(_same_stat_version(info, path_after))

    def test_self_consistent_forged_sidecar_cannot_promote_parsed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / ARTIFACT_NAME
            artifact.write_bytes(FODS)
            info = artifact.stat()
            identity = list(_identity(info))
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
