"""Fresh finite report/cleanup contract fixtures; no GUI or model execution."""
import ast
import contextlib
import copy
import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

import report_publication as publication

SOURCE = Path(os.environ.get('CONSUMER_SOURCE', Path(__file__).with_name('adaptive_semantic_repair_live_v2.py')))
loader = importlib.machinery.SourceFileLoader('custody_consumer_fixture', str(SOURCE))
spec = importlib.util.spec_from_loader(loader.name, loader)
consumer = importlib.util.module_from_spec(spec)
loader.exec_module(consumer)


def diagnostic():
    return {'outcome':'TASK_SUCCEEDED','task_effect':'succeeded',
            'delivery':'confirmed','execution_progress':{'status':'completed'},
            'input_authority':'consumed_by_recorded_execute_stage',
            'accounting':{'cost':None}, 'model_call_ledger':[]}


class ReportCustodyTests(unittest.TestCase):
    def initialization_failure(self, root, executor_error=False):
        session = Mock(name='owned_session')
        session.tmp = root/'owned-session'
        session.tmp.mkdir()
        self.assertTrue(session.tmp.resolve().is_relative_to(root.resolve()))
        session.name = 'fake-display-not-opened'
        backend = Mock(name='fake_backend')
        backend.snapshot.side_effect = RuntimeError('initial snapshot unavailable')
        backend.owner.records = []
        controller = Mock(name='fake_display')
        executor = Mock(name='fake_executor')
        if executor_error: executor.close.side_effect = OSError('executor close unavailable')
        delivery, server = Mock(), Mock()
        suite = types.SimpleNamespace(Session=lambda:session,
            prepare=lambda *args: ({},root/'absent-effect.txt',server))
        modules = {
            'executor_v13':types.SimpleNamespace(Executor=lambda *args:executor),
            'executor_v11':types.SimpleNamespace(program_sha256=None),
            'post_model_target_revalidation_v1':types.SimpleNamespace(receipt=None),
            'release_event_socket_v3':types.SimpleNamespace(ReleaseEventSocket=lambda:delivery),
            'scoped_target_handle_v1':types.SimpleNamespace(TargetHandleStore=None),
            'semantic_grounding_admission_v1':types.SimpleNamespace(admit=None),
            'semantic_probe_backend_v3':types.SimpleNamespace(Backend=lambda *args:backend,suite=suite),
            'semantic_repair_model_v2':types.SimpleNamespace(invoke=Mock(side_effect=AssertionError('model must not run'))),
            'target_handle_semantic_binding_v1':types.SimpleNamespace(derive_contract=None,repair_contract=None),
            'target_relative_crop_semantic_probe_v1':types.SimpleNamespace(score_path=None),
            'unix_json_deadline':types.SimpleNamespace(exchange=None),
            'Xlib':types.SimpleNamespace(display=types.SimpleNamespace(Display=lambda *args:controller)),
        }
        with patch.dict('sys.modules',modules):
            result = consumer.run_case({'seed':1,'chromium':'not-launched'},root,0,'local')
        return result, controller, backend, session, delivery, server

    def test_initial_failure_closes_display_before_geometry_exists(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result,controller,*_=self.initialization_failure(root)
            controller.close.assert_called_once_with()
            self.assertEqual(result['status'],'FAILED')
            self.assertFalse(result['passed'])
            self.assertEqual(publication.read_retained_report(root/'case-01-local')['error'],result['error'])

    def test_cleanup_failure_preserves_cause_and_attempts_later_closes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            result,controller,backend,session,delivery,server=self.initialization_failure(root,True)
            for resource in (controller,backend,session,delivery):resource.close.assert_called_once_with()
            server.shutdown.assert_called_once_with();server.server_close.assert_called_once_with()
            self.assertEqual(result['cleanup_errors'],[{'stage':'executor_close','type':'OSError','message':'executor close unavailable'}])
            self.assertIn('initial snapshot unavailable',result['error'])
            self.assertEqual(result['report_retention']['status'],'RETAINED')
            self.assertFalse(result['passed'])

    def test_returned_receipt_survives_post_return_processing_error(self):
        tree=ast.parse(SOURCE.read_text())
        run_case=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_case')
        block=next(n for n in run_case.body if isinstance(n,ast.Try))
        index=next(i for i,n in enumerate(block.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='adaptive' for t in n.targets))
        prefix=[]
        for node in block.body[index+1:]:
            prefix.append(node)
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='recovery_completed_ns' for t in node.targets):break
        failure=ast.parse("raise RuntimeError('processing failed after caller return')").body[0]
        probe=ast.FunctionDef(name='probe',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),decorator_list=[],body=[ast.Try(body=[*prefix,failure],handlers=copy.deepcopy(block.handlers),orelse=[],finalbody=copy.deepcopy(block.finalbody))])
        with tempfile.TemporaryDirectory() as temp:
            original=diagnostic();report={}
            namespace=dict(vars(consumer),adaptive=original,report=report,case=Path(temp),threads=[],executor=None,controller=None,original_geometry=None,backend=None,output=None,app_server=None,session=None,delivery=Mock(),events=[])
            exec(compile(ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[])),'selected-post-return-contract','exec'),namespace)
            namespace['probe']()
            directory=Path(temp)
            snapshot=(publication.read_retained_report(directory) if (directory/'report.retention.json').exists()
                      else json.loads((directory/'report.json').read_bytes()))
            self.assertEqual(snapshot['adaptive'],original)
            self.assertFalse(report['passed'])
            self.assertEqual(original,diagnostic())

    def test_output_exists_error_does_not_skip_later_cleanup_or_report(self):
        tree=ast.parse(SOURCE.read_text())
        run_case=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_case')
        block=next(n for n in run_case.body if isinstance(n,ast.Try))
        probe=ast.FunctionDef(name='probe',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),decorator_list=[],body=copy.deepcopy(block.finalbody))
        with tempfile.TemporaryDirectory() as temp:
            case=Path(temp);delivery=Mock();server=Mock()
            output=Mock();output.exists.side_effect=PermissionError('output existence unavailable')
            original=diagnostic();report={'status':'COMPLETED','passed':True,'adaptive':original}
            namespace=dict(vars(consumer),report=report,case=case,threads=[],executor=None,controller=None,original_geometry=None,backend=None,output=output,app_server=server,session=None,delivery=delivery,events=[])
            exec(compile(ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[])),'selected-existence-cleanup-contract','exec'),namespace)
            namespace['probe']()
            delivery.close.assert_called_once_with()
            server.shutdown.assert_called_once_with();server.server_close.assert_called_once_with()
            self.assertEqual(report['cleanup_errors'],[{'stage':'output_copy','type':'PermissionError','message':'output existence unavailable'}])
            saved=publication.read_retained_report(case)
            self.assertEqual(saved['adaptive'],original)
            self.assertEqual(saved['status'],'FAILED');self.assertIs(saved['passed'],False)

    def test_large_plain_report_and_huge_integer_keep_original_values(self):
        for value in ('x'*240000,2**16384):
            with self.subTest(type=type(value).__name__),tempfile.TemporaryDirectory() as temp:
                report={'schema':'fresh-custody-fixture','passed':True,'adaptive':diagnostic(),'original_value':value}
                result=publication.publish_report(report,Path(temp))
                self.assertEqual(result['status'],'RETAINED')
                restored=publication.read_retained_report(Path(temp))
                self.assertEqual(restored,report)
                self.assertIs(type(restored['original_value']),type(value))
                self.assertIs(result['grants_input_authority'],False)

    def exercise_main(self, root, fail_root):
        output=root/'output';order=['local','model'];calls=[]
        (root/'adaptive_semantic_repair_live_v2_prereg.json').write_text(json.dumps({'order':order,'scope':'fresh contract fixture'}))
        real_write=publication.write_report
        def writer(report,directory,**options):
            if not fail_root and Path(directory).name=='case-0':
                raise OSError('injected publication unavailable')
            return real_write(report,directory,**options)
        real_open=Path.open
        def fault_open(path,*args,**kwargs):
            if fail_root and path.parent==output and path.name in ('report.json','report.lossless.json'):
                raise OSError('injected root report write unavailable')
            return real_open(path,*args,**kwargs)
        def fake_case(plan,directory,ordinal,mode):
            calls.append(mode);case=directory/('case-'+str(ordinal));case.mkdir()
            report={'mode':mode,'status':'COMPLETED','passed':True,'adaptive':diagnostic()}
            report['report_retention']=publication.publish_report(report,case)
            return report
        console=io.StringIO()
        with patch.object(consumer,'HERE',root),patch.object(consumer,'OUT',output),patch.object(consumer,'run_case',fake_case),patch.object(publication,'write_report',writer),patch.object(Path,'open',fault_open),contextlib.redirect_stdout(console):consumer.main()
        return calls,json.loads(console.getvalue())

    def test_unconfirmed_case_publication_stops_next_case(self):
        with tempfile.TemporaryDirectory() as temp:
            calls,result=self.exercise_main(Path(temp),False)
            self.assertEqual(calls,['local'])
            self.assertFalse(result['passed'])

    def test_unconfirmed_root_publication_does_not_print_success(self):
        with tempfile.TemporaryDirectory() as temp:
            calls,result=self.exercise_main(Path(temp),True)
            self.assertEqual(calls,['local','model'])
            self.assertFalse(result['passed'])
            self.assertEqual(result['report_retention']['status'],'RETENTION_UNCONFIRMED')

    def test_over_bound_and_nonfinite_reports_refuse_without_artifact(self):
        for value in ('x'*publication.REPORT_LIMIT,float('nan')):
            with tempfile.TemporaryDirectory() as temp:
                result=publication.publish_report({'value':value},Path(temp))
                self.assertEqual(result['status'],'RETENTION_UNCONFIRMED')
                self.assertEqual(list(Path(temp).iterdir()),[])


if __name__=='__main__':unittest.main()
