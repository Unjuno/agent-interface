"""Offline composition of completed compiled actions with G10 save custody.

The bridge and saved FODS contents are fixtures; this checks callback ordering
and receipt joins, not a live Calc launch or save.
"""
import copy
import tempfile
import unittest
from pathlib import Path

from runtime.guarded_x11_v1.calc_g10_artifact_v1 import (
    CalcG10ArtifactCustody, PROFILE_ID,
    make_registered_calc_g10_save_controller_receipt,
)
from runtime.guarded_x11_v1.process_identity import process_generation_from_identity
from runtime.guarded_x11_v1.test_compiled import (
    Bridge, bindings as compiled_bindings, perceive, run, spec, verify,
)


CALL_ID = 'c' * 32
ATTEMPT_ID = 'g10-action-hook-composition'
XID, PID, START_TICKS = 42, 4321, 98765
PROCESS_GENERATION = process_generation_from_identity(XID, PID, START_TICKS)
WINDOW_GENERATION = 'd' * 64
FIXTURES = (Path(__file__).resolve().parents[2] / 'research' / 'integration'
            / 'calc_current_shared_3311_4d74_20261004'
            / 'calc-compiled-ocrlive-4d74' / 'runs' / 'compiled_ocrlive10')


class G10ActionCustodyCompositionTests(unittest.TestCase):
    def test_core_release_callback_snapshots_both_rows_before_next_action(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / CALL_ID
            root.mkdir()
            custody = CalcG10ArtifactCustody(root, call_id=CALL_ID,
                attempt_id=ATTEMPT_ID)
            custody.bind_target(process_generation=PROCESS_GENERATION,
                window_generation=WINDOW_GENERATION, target_xid=XID,
                target_pid=PID, target_start_ticks=START_TICKS)

            interface = copy.deepcopy(spec())
            interface['interface_id'] = PROFILE_ID
            interface['actions'] = {
                'first': interface['actions'].pop('enter'),
                'second': interface['actions'].pop('save'),
            }
            for state in interface['method']['states'].values():
                for branch in state['branches']:
                    if branch.get('action') == 'enter':
                        branch['action'] = 'first'
                    elif branch.get('action') == 'save':
                        branch['action'] = 'second'
            old_bindings = compiled_bindings()
            action_bindings = {
                'first': old_bindings['enter'],
                'second': old_bindings['save'],
            }
            save_receipts = []

            def retain_completed(transition):
                action = transition['action']
                self.assertTrue(transition['release_verified'])
                self.assertEqual(set(custody._records),
                    set() if action == 'first' else {'first'})
                (custody.workbook_path).write_bytes(
                    (FIXTURES / f'{action}.fods').read_bytes())
                request_ns = transition['execution_accepted_ns']
                request = {
                    'schema': 'agent-interface/calc-g10-save-request-v1',
                    'call_id': CALL_ID, 'attempt_id': ATTEMPT_ID,
                    'profile_id': PROFILE_ID, 'action': action,
                    'action_id': transition['action_id'],
                    'process_generation': PROCESS_GENERATION,
                    'window_generation': WINDOW_GENERATION,
                    'save_request_id': ('1' if action == 'first' else '2') * 32,
                    'save_request_monotonic_ns': request_ns,
                }
                save_receipts.append(custody.record_saved_action(action,
                    action_receipt={'action': action,
                        'action_id': transition['action_id'],
                        'status': 'completed', 'release_verified': True},
                    save_request=request))

            result = run(Bridge(), interface, action_bindings,
                perceive=perceive, verify_effect=verify,
                on_action_completed=retain_completed)
            self.assertEqual(result['outcome'], 'TASK_SUCCEEDED')
            self.assertEqual([row['action'] for row in result['transitions']],
                             ['first', 'second'])
            controller = make_registered_calc_g10_save_controller_receipt(
                descriptor=custody.descriptor,
                method_receipt=result,
                save_receipts=save_receipts)
            self.assertIsNotNone(controller)
            exit_ns = max(row['execution_accepted_ns']
                          for row in result['transitions']) + 1_000_000_000
            verified = custody.verify_after_close(method_receipt=result,
                trusted_save_controller_receipt=controller,
                close_receipt={'status':'closed','verified':True,
                    'owner_process_retired':True,'release_confirmed':True},
                target_exit_receipt={
                    'schema':'agent-interface/calc-target-exit-receipt-v1',
                    'status':'exited','verified':True,
                    'process_generation':PROCESS_GENERATION,'xid':XID,
                    'pid':PID,'start_ticks':START_TICKS,'exit_code':0,
                    'observed_monotonic_ns':exit_ns})
            self.assertEqual(verified['status'], 'verified')
            self.assertIs(verified['task_success'], True)
            self.assertEqual(set(verified['saved_effects']), {'first', 'second'})


if __name__ == '__main__':
    unittest.main()
