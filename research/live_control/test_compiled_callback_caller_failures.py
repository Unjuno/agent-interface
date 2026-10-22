"""Callback receipt failures through guarded composition, no native transport."""
import copy
import importlib
import json
import unittest
from unittest.mock import patch
from runtime.guarded_x11_v1 import compiled
from runtime.guarded_x11_v1 import test_compiled as memory
from research.live_control import test_compiled_native_caller_composition as fixture

ROWS=[]


class CallbackCallerFailureTests(unittest.TestCase):
    def test_guarded_adapter_retains_verifier_witness_before_core_receipt(self):
        bridge=memory.Bridge()
        def failed(*args):raise RuntimeError('owned verifier unavailable')
        result=compiled.run(bridge,memory.spec(),memory.bindings(),perceive=memory.perceive,verify_effect=failed)
        witnesses=[v for n,v in bridge.saved if n.endswith('-exception.json')]
        self.assertEqual(len(witnesses),1);self.assertEqual(witnesses[0]['stage'],'effect_verification')
        self.assertEqual((result['outcome'],result['reason']),('RUNTIME_FAILED','effect_unavailable'))
        self.assertEqual(result['completed_transitions'],1);self.assertEqual(len(bridge.inputs),1)
        self.assertEqual([v for n,v in bridge.saved if n.endswith('-receipt.json')],[result])
        ROWS.append(dict(case='memory-verifier',result=result,witnesses=witnesses,saved=bridge.saved,inputs=bridge.inputs))

    def cell(self,verifier=False,journal_at=None):
        module=importlib.import_module('research.live_control.integrated_efficiency_compiled_execution_v2')
        original_init=compiled._Adapter.__init__;original_run=module.run_compiled;events=[]
        def initialize(adapter,*args,**kwargs):
            original_init(adapter,*args,**kwargs)
            if verifier:
                def failed(*args):raise RuntimeError('owned native-caller verifier unavailable')
                adapter.verifier=failed
        def run(interface,adapters):
            def journal(event):
                events.append(copy.deepcopy(event))
                if event['event']==journal_at:raise OSError('owned core journal unavailable')
            return original_run(interface,dict(adapters,journal=journal))
        case=fixture.CompiledNativeCallerTests()
        try:
            with patch.object(compiled._Adapter,'__init__',initialize),patch.object(module,'run_compiled',run):
                row=case.cell()
        finally:case.doCleanups()
        row.update(case='native-caller',verifier_failure=verifier,journal_at=journal_at,core_events=events)
        ROWS.append(row)
        r=row['result'];core=r['compiled_execution_receipt']
        self.assertEqual(r['outcome'],'EXECUTION_INCOMPLETE')
        self.assertEqual(r['execution_progress']['completed_actions'],1)
        self.assertEqual(core['outcome'],'RUNTIME_FAILED');self.assertEqual(core['completed_transitions'],1)
        self.assertEqual(row['emissions'],[(2,1),(2,2),(3,2),(3,1)])
        self.assertEqual(row['outer_checks'],[])
        failures=[e for e in core['critical_events'] if e['event']=='journal_write_failed']
        self.assertEqual(len(failures),int(journal_at is not None))
        exceptions=[json.loads(bytes.fromhex(v)) for n,v in row['native_files_hex'].items() if n.endswith('-exception.json')]
        self.assertEqual(len(exceptions),int(verifier))
        if verifier:self.assertEqual(exceptions[0]['stage'],'effect_verification')
        return row

    def test_native_caller_verifier_failure_keeps_prefix(self):self.cell(verifier=True)
    def test_native_caller_journal_failure_keeps_prefix(self):self.cell(journal_at='action_terminal')
    def test_native_caller_terminal_journal_and_verifier_failures_both_survive(self):
        self.cell(verifier=True,journal_at='runtime_finished')


if __name__=='__main__':unittest.main()
