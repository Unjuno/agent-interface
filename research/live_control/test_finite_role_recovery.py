"""Portable public-state regressions; no native inputs or model calls."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finite_role_recovery import StaleDocument, run_with_one_recovery

ROLE = '当日の議論を議事録にまとめる担当'
NEW_ROLE = '会議中の意見と決定を記録する係'
DOCUMENT = ('回復の検査 é🚀\r\n' + ROLE + '：加藤\r\n'
            '会場の受付担当：加藤\r\n引用：「加藤さんの旧稿を保存する」\r\n'
            '注記：次回の日程は確定済み。\r\n')
TASK = dict(id='portable-control', document=DOCUMENT, old_person='加藤', new_person='森')


class Editor:
    def __init__(self, kind):
        self.kind = kind
        self.body = self.disk = DOCUMENT
        self.reads = self.replacements = self.saves = 0

    def read_current(self):
        self.reads += 1
        if self.reads == 1 and self.kind == 'initial_wrong_tab':
            raise RuntimeError('STOP: wrong initial tab')
        if self.reads == 2 and self.kind in ('wrong_tab', 'unknown'):
            raise RuntimeError('STOP: ' + self.kind)
        if self.reads == 3 and self.kind == 'typed_stale_after_replace':
            raise StaleDocument('STOP: changed after replacement')
        if self.reads == 5 and self.kind == 'twice':
            self.body = self.body.replace('注記：', '再変更：')
        return self.body

    def replace_once(self, text):
        self.replacements += 1
        self.body = text
        if self.kind == 'unknown_replace':
            raise RuntimeError('STOP: replacement result unknown')

    def save_once(self):
        self.saves += 1
        self.disk = self.body
        if self.kind == 'withheld_save':
            raise RuntimeError('STOP: save result unknown')
        if self.kind == 'typed_stale_after_save':
            raise StaleDocument('STOP: changed after save attempt')


class FiniteRoleRecoveryTests(unittest.TestCase):
    def check_case(self, kind, reuse=True):
        editor = Editor(kind)
        if kind == 'initial_mismatch':
            editor.body += '追加の本文\r\n'
        calls, events = [], []

        def infer(task, document):
            calls.append(document)
            role = NEW_ROLE if NEW_ROLE in document else ROLE
            output = dict(updated_text=document.replace(role + '：加藤', role + '：森'),
                          changed_role=role, previous_person='加藤', new_person='森',
                          untouched_title='sibling.txt')
            if kind == 'collateral':
                output['updated_text'] = output['updated_text'].replace('受付担当：加藤', '受付担当：森')
            if len(calls) == 1 and kind in ('annotation', 'twice', 'role_change'):
                editor.body = editor.body.replace('次回の日程は確定済み。', '追加した情報を保持。')
                if kind == 'role_change':
                    editor.body = editor.body.replace(ROLE, NEW_ROLE)
            return output

        error = None
        try:
            run_with_one_recovery(TASK, editor, infer,
                                  lambda event, data: events.append(event), reuse)
        except RuntimeError as exc:
            error = exc
        stopped = kind in ('twice', 'wrong_tab', 'unknown', 'withheld_save',
                           'unknown_replace', 'collateral', 'initial_mismatch',
                           'initial_wrong_tab', 'typed_stale_after_replace', 'typed_stale_after_save')
        self.assertEqual(error is not None, stopped)
        inputs = 0 if kind in ('twice', 'wrong_tab', 'unknown', 'collateral',
                               'initial_mismatch', 'initial_wrong_tab') else 1
        self.assertEqual(editor.replacements, inputs)
        self.assertEqual(editor.saves, 0 if kind in ('unknown_replace', 'typed_stale_after_replace') else inputs)
        expected_calls = 2 if kind == 'role_change' or not reuse else 1
        if kind in ('initial_mismatch', 'initial_wrong_tab'):
            expected_calls = 0
        self.assertEqual(len(calls), expected_calls)
        self.assertEqual(events.count('one_recovery_admitted'),
                         int(kind in ('annotation', 'twice', 'role_change')))
        self.assertEqual(events.count('save_returned'), int(not stopped))
        if kind == 'twice':
            self.assertIsInstance(error, StaleDocument)
            self.assertEqual(editor.disk, DOCUMENT)
        if not stopped:
            role = NEW_ROLE if kind == 'role_change' else ROLE
            expected = DOCUMENT.replace(ROLE, role).replace(role + '：加藤', role + '：森')
            if kind in ('annotation', 'role_change'):
                expected = expected.replace('次回の日程は確定済み。', '追加した情報を保持。')
            self.assertEqual(editor.disk.encode('utf-8'), expected.encode('utf-8'))
        return events

    def test_normal_exact_effect(self):
        self.check_case('normal')

    def test_annotation_retained_without_second_subject_call(self):
        self.check_case('annotation')

    def test_second_change_stops_before_controller_input(self):
        self.check_case('twice')

    def test_wrong_tab_never_recovers(self):
        self.check_case('wrong_tab')

    def test_unknown_observation_never_recovers(self):
        self.check_case('unknown')

    def test_changed_role_invalidates_before_input(self):
        events = self.check_case('role_change')
        self.assertLess(events.index('invalidated_before_input'), events.index('replacement_intent'))

    def test_unknown_save_no_resend_or_success(self):
        self.check_case('withheld_save')

    def test_unknown_replacement_no_save_or_resend(self):
        self.check_case('unknown_replace')

    def test_fresh_model_replan_baseline(self):
        self.check_case('annotation', reuse=False)

    def test_collateral_change_refused_before_input(self):
        self.check_case('collateral')

    def test_initial_body_mismatch_no_model_or_input(self):
        self.check_case('initial_mismatch')

    def test_initial_wrong_tab_no_model_or_input(self):
        self.check_case('initial_wrong_tab')

    def test_typed_stale_after_replacement_cannot_authorize_recovery(self):
        self.check_case('typed_stale_after_replace')

    def test_typed_stale_after_save_cannot_authorize_recovery(self):
        self.check_case('typed_stale_after_save')


if __name__ == '__main__':
    unittest.main()
