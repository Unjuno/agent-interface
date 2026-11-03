"""Call-owned Calc artifact admission refuses stale and unowned results."""
import tempfile
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.calc_effect_v1 import ARTIFACT_NAME
from runtime.guarded_x11_v1.calc_profile_v1 import verify_saved_fods_bytes
from runtime.guarded_x11_v1.calc_task_artifact_v1 import (
    CalcTaskArtifact,make_registered_calc_save_controller_receipt,
    verify_task_artifact_descriptor)
from runtime.guarded_x11_v1.process_identity import process_generation_from_identity


CALL_ID = '1' * 32
ATTEMPT_ID = 'artifact-test-01'
TARGET_XID = 20
TARGET_PID = 4321
TARGET_START_TICKS = 98765
PROCESS_GENERATION = process_generation_from_identity(
    TARGET_XID,TARGET_PID,TARGET_START_TICKS)
WINDOW_GENERATION = 'b' * 64
CLOSE = {'status':'closed', 'verified':True,
         'owner_process_retired':True, 'release_confirmed':True}
TARGET_EXIT = {'schema':'agent-interface/calc-target-exit-receipt-v1',
    'status':'exited','verified':True,'process_generation':PROCESS_GENERATION,
    'xid':TARGET_XID,'pid':TARGET_PID,'start_ticks':TARGET_START_TICKS,
    'exit_code':0,'observed_monotonic_ns':123456789}
WRAPPED_EXIT = {'schema':'agent-interface/calc-target-exit-receipt-v2',
    'custody':'libreoffice-oosplash-direct-child-v1',
    'launcher_pid':9876,'launcher_start_ticks':1234,
    'launcher_executable':'/usr/lib/libreoffice/program/oosplash',
    'launcher_package_version':'4:7.4.7-1+deb12u14',
    'launcher_exit_code':0,'replacement_observed':False}
FODS = (b'<?xml version="1.0"?><office:document-content '
    b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    b'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    b'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
    b'<office:body><office:spreadsheet><table:table table:name="Sheet1">'
    b'<table:table-row><table:table-cell office:value-type="float" office:value="731"/>'
    b'</table:table-row><table:table-row>'
    b'<table:table-cell office:value-type="float" office:value="864"/>'
    b'</table:table-row></table:table></office:spreadsheet></office:body>'
    b'</office:document-content>')


def new_artifact(directory, **kwargs):
    call_root = Path(directory) / CALL_ID
    call_root.mkdir(exist_ok=True)
    return CalcTaskArtifact(call_root, call_id=CALL_ID, attempt_id=ATTEMPT_ID,
        process_generation=PROCESS_GENERATION,
        window_generation=WINDOW_GENERATION,target_xid=TARGET_XID,
        target_pid=TARGET_PID,target_start_ticks=TARGET_START_TICKS, **kwargs)


def exit_after(artifact, **updates):
    request_ns = artifact._save_request_ns
    return dict(TARGET_EXIT,
        observed_monotonic_ns=request_ns + 1, **updates)


def successful_registered_profile_receipt():
    enter_id, save_id = 'action-' + '1' * 32, 'action-' + '2' * 32
    return {'format':'compiled-gui-runtime-receipt-v1',
        'interface_id':'calc-ocr-save-v1','method':'calc-ocr-save-v1',
        'method_version':'1','outcome':'SAFE_YIELD',
        'reason':'effect_unavailable','completed_transitions':2,
        'transitions':[{'action':'enter','release_verified':True},
                       {'action':'save','release_verified':True}],
        'critical_events':[
            {'event':'branch_selected','state':'initial','action':'enter',
             'outcome':'action','matched_conditions':{'blank':True,'context_ok':True}},
            {'event':'action_terminal','action':'enter','action_id':enter_id,
             'status':'completed','release_verified':True},
            {'event':'effect_checked','action':'enter','action_id':enter_id,
             'status':'succeeded'},
            {'event':'branch_selected','state':'filled','action':'save',
             'outcome':'action','matched_conditions':{'cells_filled':True,'context_ok':True}},
            {'event':'action_terminal','action':'save','action_id':save_id,
             'status':'completed','release_verified':True},
            {'event':'effect_checked','action':'save','action_id':save_id,
             'status':'unavailable','effect_verification_started_ns':100,
             'effect_verification_accepted_ns':200},
            {'event':'runtime_finished','outcome':'SAFE_YIELD',
             'reason':'effect_unavailable'}]}


class CalcTaskArtifactTests(unittest.TestCase):
    def test_reserved_blank_is_flat_odf_spreadsheet_not_content_xml_fragment(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            data = artifact.path.read_bytes()
        self.assertIn(b'<office:document ', data)
        self.assertIn(b'office:mimetype="application/vnd.oasis.opendocument.spreadsheet"',
                      data)
        self.assertNotIn(b'<office:document-content', data)
        parsed = verify_saved_fods_bytes(data)
        self.assertEqual(parsed['status'], 'failed', parsed)
        self.assertEqual(parsed['reason'], 'populated_cell_set_mismatch', parsed)
        self.assertFalse(parsed['task_success'], parsed)

    def test_reservation_can_precede_one_time_target_generation_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            call_root = Path(directory) / CALL_ID
            call_root.mkdir()
            artifact = CalcTaskArtifact(call_root, call_id=CALL_ID,
                attempt_id=ATTEMPT_ID)
            self.assertTrue(artifact.path.is_file())
            with self.assertRaisesRegex(ValueError, 'not bound'):
                _ = artifact.descriptor
            with self.assertRaisesRegex(ValueError, 'duplicate, terminal'):
                artifact.record_save_request(process_generation=PROCESS_GENERATION,
                    window_generation=WINDOW_GENERATION)
            artifact.bind_target(process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION,target_xid=TARGET_XID,
                target_pid=TARGET_PID,target_start_ticks=TARGET_START_TICKS)
            self.assertEqual(artifact.descriptor['process_generation'],
                             PROCESS_GENERATION)
            self.assertEqual(artifact.descriptor['window_generation'],
                             WINDOW_GENERATION)
            with self.assertRaises(AttributeError):
                artifact.process_generation = 'c' * 64
            with self.assertRaisesRegex(ValueError, 'already bound'):
                artifact.bind_target(process_generation='c' * 64,
                    window_generation='d' * 64,target_xid=TARGET_XID,
                    target_pid=TARGET_PID,target_start_ticks=TARGET_START_TICKS)

    def test_bound_descriptor_identity_fields_must_reproduce_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            call_root=Path(directory)/CALL_ID
            call_root.mkdir()
            with self.assertRaisesRegex(ValueError,'do not match process generation'):
                CalcTaskArtifact(call_root,call_id=CALL_ID,attempt_id=ATTEMPT_ID,
                    process_generation=PROCESS_GENERATION,
                    window_generation=WINDOW_GENERATION,target_xid=TARGET_XID,
                    target_pid=TARGET_PID+1,target_start_ticks=TARGET_START_TICKS)
            self.assertFalse((call_root/ARTIFACT_NAME).exists())

    def test_binding_refuses_changed_reserved_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            call_root = Path(directory) / CALL_ID
            call_root.mkdir()
            artifact = CalcTaskArtifact(call_root, call_id=CALL_ID,
                attempt_id=ATTEMPT_ID)
            artifact.path.write_bytes(FODS)
            with self.assertRaisesRegex(ValueError, 'changed before target binding'):
                artifact.bind_target(process_generation=PROCESS_GENERATION,
                    window_generation=WINDOW_GENERATION,target_xid=TARGET_XID,
                    target_pid=TARGET_PID,target_start_ticks=TARGET_START_TICKS)
            with self.assertRaisesRegex(ValueError, 'not bound'):
                _ = artifact.descriptor

    def test_closed_unbound_artifact_stays_unknown_even_if_parsable(self):
        with tempfile.TemporaryDirectory() as directory:
            call_root = Path(directory) / CALL_ID
            call_root.mkdir()
            artifact = CalcTaskArtifact(call_root, call_id=CALL_ID,
                attempt_id=ATTEMPT_ID)
            artifact.path.write_bytes(FODS)
            result = artifact.verify_after_close(CLOSE)
        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'target_generation_unbound', result)
        self.assertIsNone(result['task_success'], result)

    def test_reserves_unique_blank_bound_to_call_and_target_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            self.assertEqual(Path(directory) / CALL_ID / ARTIFACT_NAME,
                             artifact.path)
            self.assertEqual(artifact.descriptor['process_generation'],
                             PROCESS_GENERATION)
            self.assertEqual(artifact.descriptor['window_generation'],
                             WINDOW_GENERATION)
            with self.assertRaises(FileExistsError):
                new_artifact(directory)

    def test_parsed_bytes_do_not_claim_gui_effect_without_trusted_controller(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            artifact.record_save_request(process_generation=PROCESS_GENERATION,
                                        window_generation=WINDOW_GENERATION)
            before_close = artifact.verify_after_close(dict(CLOSE, verified=False))
            self.assertEqual(before_close['reason'], 'verified_close_required')
            (Path(directory) / CALL_ID / ARTIFACT_NAME).write_bytes(FODS)
            missing_exit = artifact.verify_after_close(CLOSE)
            self.assertEqual(missing_exit['reason'],
                             'target_process_exit_required', missing_exit)
            result = artifact.verify_after_close(CLOSE, exit_after(artifact))
            self.assertEqual(result['status'], 'unknown', result)
            self.assertIsNone(result['task_success'], result)
            self.assertEqual(result['reason'],
                             'trusted_save_controller_unavailable', result)
            self.assertEqual(result['parsed_effect']['status'], 'verified', result)
            self.assertEqual(result['call_id'], CALL_ID)
            self.assertEqual(result['attempt_id'], ATTEMPT_ID)
            self.assertEqual(result['process_generation'], PROCESS_GENERATION)
            self.assertEqual(result['window_generation'], WINDOW_GENERATION)

    def test_parent_minted_registered_save_receipt_verifies_exact_closed_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory, clock=lambda:150)
            request = artifact.record_save_request(
                process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            method = successful_registered_profile_receipt()
            controller = make_registered_calc_save_controller_receipt(
                descriptor=artifact.descriptor,method_receipt=method,
                save_request=request)
            self.assertIsInstance(controller,dict)
            (Path(directory) / CALL_ID / ARTIFACT_NAME).write_bytes(FODS)
            result = artifact.verify_after_close(CLOSE,
                dict(TARGET_EXIT,observed_monotonic_ns=250),controller)
        self.assertEqual((result['status'],result['task_success']),('verified',True),result)
        self.assertEqual(result['parsed_effect']['cells'],{'A1':'731','A2':'864'})
        self.assertEqual(result['save_controller']['save_action_id'],
                         'action-' + '2' * 32)

    def test_registered_save_receipt_refuses_missing_release_or_effect_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory, clock=lambda:150)
            request = artifact.record_save_request(
                process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            method = successful_registered_profile_receipt()
            method['critical_events'][4]['release_verified'] = False
            bad_release = make_registered_calc_save_controller_receipt(
                descriptor=artifact.descriptor,method_receipt=method,
                save_request=request)
            method = successful_registered_profile_receipt()
            method['critical_events'][2]['status'] = 'unavailable'
            bad_effect = make_registered_calc_save_controller_receipt(
                descriptor=artifact.descriptor,method_receipt=method,
                save_request=request)
        self.assertIsNone(bad_release)
        self.assertIsNone(bad_effect)

    def test_target_process_exit_must_match_admitted_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            artifact.record_save_request(process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            (Path(directory) / CALL_ID / ARTIFACT_NAME).write_bytes(FODS)
            wrong = dict(TARGET_EXIT, process_generation='c' * 64)
            result = artifact.verify_after_close(CLOSE, wrong)
        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'target_process_exit_invalid', result)
        self.assertIsNone(result['task_success'], result)

    def test_target_exit_receipt_pid_and_start_ticks_must_match_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            artifact.record_save_request(process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            (Path(directory) / CALL_ID / ARTIFACT_NAME).write_bytes(FODS)
            wrong_pid=exit_after(artifact,pid=TARGET_PID+1)
            wrong_ticks=exit_after(artifact,start_ticks=TARGET_START_TICKS+1)
            pid_result=artifact.verify_after_close(CLOSE,wrong_pid)
            ticks_result=artifact.verify_after_close(CLOSE,wrong_ticks)
        self.assertEqual(pid_result['reason'],'target_process_exit_invalid',pid_result)
        self.assertEqual(ticks_result['reason'],'target_process_exit_invalid',ticks_result)

    def test_descriptor_target_tuple_must_reproduce_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact=new_artifact(directory)
            request=artifact.record_save_request(
                process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            (Path(directory)/CALL_ID/ARTIFACT_NAME).write_bytes(FODS)
            descriptor=dict(artifact.descriptor,target_pid=TARGET_PID+1)
            result=verify_task_artifact_descriptor(Path(directory)/CALL_ID,
                descriptor=descriptor,save_request=request,
                close_receipt=CLOSE,
                target_exit_receipt=exit_after(artifact))
        self.assertEqual(result['status'],'unknown',result)
        self.assertEqual(result['reason'],'artifact_target_identity_invalid',result)
        self.assertIsNone(result['task_success'],result)

    def test_target_process_exit_must_follow_save_and_be_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            request = artifact.record_save_request(
                process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            (Path(directory) / CALL_ID / ARTIFACT_NAME).write_bytes(FODS)
            early = dict(TARGET_EXIT,
                observed_monotonic_ns=request['save_request_monotonic_ns'])
            early_result = artifact.verify_after_close(CLOSE, early)
            unclean = exit_after(artifact, exit_code=9)
            unclean_result = artifact.verify_after_close(CLOSE, unclean)
        self.assertEqual(early_result['reason'],
                         'target_exit_before_save_request', early_result)
        self.assertEqual(unclean_result['reason'],
                         'target_process_exit_invalid', unclean_result)

    def test_pinned_oosplash_child_receipt_is_distinct_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            artifact.record_save_request(process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            (Path(directory) / CALL_ID / ARTIFACT_NAME).write_bytes(FODS)
            accepted = artifact.verify_after_close(CLOSE,
                exit_after(artifact, **WRAPPED_EXIT))
            replaced_root = Path(directory) / 'replaced'
            replaced_root.mkdir()
            replaced_artifact = new_artifact(str(replaced_root))
            replaced_artifact.record_save_request(
                process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            replaced = replaced_artifact.verify_after_close(CLOSE,
                exit_after(replaced_artifact, **dict(WRAPPED_EXIT,
                    replacement_observed=True)))
            wrong_version_root = Path(directory) / 'wrong-version'
            wrong_version_root.mkdir()
            wrong_version_artifact = new_artifact(str(wrong_version_root))
            wrong_version_artifact.record_save_request(
                process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION)
            wrong_version = wrong_version_artifact.verify_after_close(CLOSE,
                exit_after(wrong_version_artifact, **dict(WRAPPED_EXIT,
                    launcher_package_version='4:7.4.7-1+deb12u13')))
        self.assertEqual(accepted['reason'],
                         'trusted_save_controller_unavailable', accepted)
        for result in (replaced, wrong_version):
            self.assertEqual(result['reason'],
                             'target_process_exit_invalid', result)
            self.assertIsNone(result['task_success'], result)

    def test_unchanged_blank_artifact_remains_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            artifact.record_save_request(process_generation=PROCESS_GENERATION,
                                        window_generation=WINDOW_GENERATION)
            result = artifact.verify_after_close(CLOSE, exit_after(artifact))
        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'artifact_unchanged_after_save_request')
        self.assertIsNone(result['task_success'])

    def test_wrong_or_extra_cells_do_not_pass(self):
        for data in (FODS.replace(b'office:value="864"', b'office:value="865"'),
                     FODS.replace(b'</table:table-row>',
                         b'<table:table-cell office:value-type="string">'
                         b'<text:p>extra</text:p></table:table-cell></table:table-row>')):
            with self.subTest(data=data[-80:]), tempfile.TemporaryDirectory() as directory:
                artifact = new_artifact(directory)
                artifact.record_save_request(process_generation=PROCESS_GENERATION,
                                            window_generation=WINDOW_GENERATION)
                (Path(directory) / CALL_ID / ARTIFACT_NAME).write_bytes(data)
                result = artifact.verify_after_close(CLOSE, exit_after(artifact))
                self.assertEqual(result['status'], 'unknown', result)
                self.assertEqual(result['reason'], 'saved_artifact_not_scored')
                self.assertNotEqual(result['parsed_effect']['status'], 'verified')
                self.assertIsNone(result['task_success'])

    def test_changed_target_duplicate_request_and_missing_file_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = new_artifact(directory)
            with self.assertRaises(ValueError):
                artifact.record_save_request(process_generation='c' * 64,
                    window_generation=WINDOW_GENERATION)
            artifact.record_save_request(process_generation=PROCESS_GENERATION,
                                        window_generation=WINDOW_GENERATION)
            with self.assertRaises(ValueError):
                artifact.record_save_request(process_generation=PROCESS_GENERATION,
                    window_generation=WINDOW_GENERATION)
            (Path(directory) / CALL_ID / ARTIFACT_NAME).unlink()
            result = artifact.verify_after_close(CLOSE, exit_after(artifact))
        self.assertEqual(result['status'], 'unknown', result)
        self.assertEqual(result['reason'], 'artifact_missing_or_unstable')


if __name__ == '__main__':
    unittest.main()
