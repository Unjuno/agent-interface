"""Portable public-state regressions; no native inputs or model calls."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from finite_role_recovery import StaleDocument, run_with_one_recovery
from finite_role_recovery.role_method import apply_role

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


BOUNDARIES=('\r','\n','\v','\f','\x1c','\x1d','\x1e','\x85','\u2028','\u2029')
DOC='題名 é🚀\r\n役割：加藤\r\n引用：加藤の旧稿を保持\r\n'

class LineGuardTests(unittest.TestCase):
    def test_all_line_boundaries_refused_in_all_parameters_and_positions(self):
        for separator in BOUNDARIES:
            for index in range(3):
                for position in ('start','middle','end'):
                    values=['役割','加藤','森']
                    bad={'start':separator+'x','middle':'x'+separator+'y','end':'x'+separator}[position]
                    values[index]=bad
                    with self.subTest(codepoint=ord(separator),parameter=index,position=position):
                        self.assertEqual(apply_role(DOC,*values),{'outcome':'REFUSE','reason':'invalid_line_parameter'})

    def test_normal_unicode_space_tab_roundtrip_preserves_other_bytes(self):
        for new in ('森 é🚀','森\t記録係','森 Unicode'):
            with self.subTest(new=new):
                changed=apply_role(DOC,'役割','加藤',new)
                self.assertEqual(changed['outcome'],'READY')
                self.assertEqual(changed['updated_text'].encode('utf-8'),DOC.replace('役割：加藤','役割：'+new).encode('utf-8'))
                restored=apply_role(changed['updated_text'],'役割',new,'加藤')
                self.assertEqual(restored['outcome'],'READY')
                self.assertEqual(restored['updated_text'],DOC)

    def test_malformed_new_person_cannot_reach_controller_inputs(self):
        for separator in BOUNDARIES:
            with self.subTest(codepoint=ord(separator)):
                class Editor:
                    body=DOC;replacements=0;saves=0
                    def read_current(self):return self.body
                    def replace_once(self,text):self.replacements+=1;self.body=text
                    def save_once(self):self.saves+=1
                editor=Editor();new='森'+separator+'追加'
                task=dict(id='line-control',document=DOC,old_person='加藤',new_person=new)
                events=[]
                def subject(task,document):
                    return dict(updated_text=document.replace('役割：加藤','役割：'+new),changed_role='役割',
                        previous_person='加藤',new_person=new,untouched_title='sibling.txt')
                with self.assertRaises(RuntimeError):
                    run_with_one_recovery(task,editor,subject,lambda event,data:events.append(event))
                self.assertEqual(editor.replacements,0)
                self.assertEqual(editor.saves,0)
                self.assertNotIn('replacement_intent',events)
                self.assertNotIn('one_recovery_admitted',events)

    def test_empty_and_colon_guard_preserved(self):
        for bad in ('','森：係'):
            self.assertEqual(apply_role(DOC,'役割','加藤',bad)['outcome'],'REFUSE')


class RequestCustodyTests(unittest.TestCase):
 def case(self,kind):
  mode='package_direct'
  ROLE='議事録担当'
  DOC='新しい検査\r\n議事録担当：安田\r\n受付担当：安田\r\n注記：元の本文\r\n'
  task=dict(id='custody-fixed',document=DOC,old_person='安田',new_person='田島')
  original=dict(task);events=[];calls=[]
  class Editor:
   replacements=saves=0
   body=disk=DOC
   def read_current(self):return self.body
   def replace_once(self,text):self.replacements+=1;self.body=text
   def save_once(self):self.saves+=1;self.disk=self.body
  editor=Editor()
  def subject(t,document):
   calls.append(dict(t))
   if kind in ('argument_first','external_first','external_first_return_alias') and len(calls)==1:
    (t if kind=='argument_first' else task)['new_person']='石井'
   if kind in ('argument_recovery','external_recovery') and len(calls)==2:
    (t if kind=='argument_recovery' else task)['new_person']='石井'
   if kind.endswith('recovery') and len(calls)==1:editor.body=editor.body.replace('元の本文','更新された注記')
   source=task if kind=='external_first_return_alias' else t
   return dict(updated_text=document.replace(ROLE+'：'+source['old_person'],ROLE+'：'+source['new_person']),changed_role=ROLE,previous_person=source['old_person'],new_person=source['new_person'],untouched_title='sibling.txt')
  outcome='RETURN';error=None
  submitted=task
  callback=subject
  try:run_with_one_recovery(submitted,editor,callback,lambda k,v:events.append([k,v]),reuse_label=False if kind.endswith('recovery') else True)
  except RuntimeError as exc:outcome='STOP';error=str(exc)
  expected=DOC.replace('議事録担当：安田','議事録担当：田島')
  if kind.endswith('recovery'):expected=expected.replace('元の本文','更新された注記')
  row=dict(kind=kind,mode=mode,original=original,caller_after=task,calls=calls,events=events,disk=editor.disk,expected=expected,replacements=editor.replacements,saves=editor.saves,outcome=outcome,error=error)

  self.assertTrue(editor.disk==expected or (outcome=='STOP' and editor.replacements==editor.saves==0),'effect differs from original request without pre-input STOP')
 def test_control(self):self.case('control')
 def test_argument_first(self):self.case('argument_first')
 def test_external_first(self):self.case('external_first')
 def test_external_first_return_alias(self):self.case('external_first_return_alias')
 def test_argument_recovery(self):self.case('argument_recovery')
 def test_external_recovery(self):self.case('external_recovery')


class OutputCustodyTests(unittest.TestCase):
 def test_validated_role_survives_journal_mutation(self):
  doc='記録担当：山口\r\n受付担当：川村\r\n注記：新しい検査\r\n'
  task=dict(id='output-custody',document=doc,old_person='山口',new_person='川村')
  output=dict(updated_text='記録担当：川村\r\n受付担当：川村\r\n注記：新しい検査\r\n',changed_role='記録担当',previous_person='山口',new_person='川村',untouched_title='sibling.txt')
  class Editor:
   replacements=saves=0
   body=disk=doc
   def read_current(self):return self.body
   def replace_once(self,text):self.replacements+=1;self.body=text
   def save_once(self):self.saves+=1;self.disk=self.body
  editor=Editor();events=[]
  def record(k,v):
   events.append([k,v])
   if k=='subject_contract':output['changed_role']='受付担当'
  label=run_with_one_recovery(task,editor,lambda t,d:output,record)
  row=dict(returned_label=label,expected_label='記録担当',disk=editor.disk,expected_disk='記録担当：川村\r\n受付担当：川村\r\n注記：新しい検査\r\n',output_after=output,events=events,replacements=editor.replacements,saves=editor.saves)

  self.assertEqual(editor.disk,row['expected_disk'])
  self.assertEqual(label,'記録担当')
 def test_dict_subclass_output_still_refuses(self):
  class Response(dict):pass
  class Editor:
   replacements=saves=0
   def read_current(self):return '記録担当：山口\r\n'
   def replace_once(self,text):self.replacements+=1
   def save_once(self):self.saves+=1
  editor=Editor()
  output=Response(updated_text='記録担当：川村\r\n',changed_role='記録担当',previous_person='山口',new_person='川村',untouched_title='sibling.txt')
  task=dict(id='subclass-refusal',document='記録担当：山口\r\n',old_person='山口',new_person='川村')
  with self.assertRaisesRegex(RuntimeError,'subject contract refusal'):
   run_with_one_recovery(task,editor,lambda t,d:output,lambda k,v:None)
  self.assertEqual(editor.replacements,0)
  self.assertEqual(editor.saves,0)


if __name__ == '__main__':
    unittest.main()
