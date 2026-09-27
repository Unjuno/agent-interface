import json, tempfile, unittest
from pathlib import Path
from replay import load_reducer, phase_input, comp_input, run

ROOT=Path(__file__).resolve().parent
REDUCER=ROOT.parent/'effect_outcome_contract_v1'/'outcome.py'

class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.mod=load_reducer(REDUCER)
    def test_small_cross_cohort_replay(self):
        phase=[
          {'id':'p1','effect_class':'stageable','phase_label':'REJECTED_PRE_EFFECT','effect_value':'old'},
          {'id':'p2','effect_class':'direct','phase_label':'EFFECT_CONTRADICTED','effect_value':'wrong'},
        ]
        comp=[{'id':'c1','initial':'old','intended':'target','final':'old','phase_result':'EFFECT_CONTRADICTED_COMPENSATED','events':[{'seq':1,'kind':'effect','value':'wrong'},{'seq':2,'kind':'compensation','value':'old'}]}]
        with tempfile.TemporaryDirectory() as td:
            t=Path(td); (t/'p.json').write_text(json.dumps(phase)); (t/'c.json').write_text(json.dumps(comp))
            r=run(REDUCER,t/'p.json',t/'c.json'); self.assertEqual(r['matched'],3); self.assertTrue(r['all_match'])
    def test_missing_history_fails_closed(self):
        m=self.mod
        with self.assertRaises(m.ContractError): m.reduce_outcome(operation_kind=m.OperationKind.DIRECT,initial_state='old',intended_state='target',current_state='wrong',terminal_phase=m.TerminalPhase.EFFECT_COMMITTED,events=[])
    def test_nonmonotone_history_fails_closed(self):
        m=self.mod
        with self.assertRaises(m.ContractError): m.reduce_outcome(operation_kind=m.OperationKind.DIRECT,initial_state='old',intended_state='target',current_state='old',terminal_phase=m.TerminalPhase.EFFECT_COMMITTED,events=[m.Event(2,m.EventKind.EFFECT,'wrong'),m.Event(1,m.EventKind.COMPENSATION,'old')])
    def test_state_history_mismatch_fails_closed(self):
        m=self.mod
        with self.assertRaises(m.ContractError): m.reduce_outcome(operation_kind=m.OperationKind.DIRECT,initial_state='old',intended_state='target',current_state='wrong',terminal_phase=m.TerminalPhase.EFFECT_COMMITTED,events=[m.Event(1,m.EventKind.EFFECT,'wrong'),m.Event(2,m.EventKind.COMPENSATION,'old')])
    def test_pre_effect_with_history_fails_closed(self):
        m=self.mod
        with self.assertRaises(m.ContractError): m.reduce_outcome(operation_kind=m.OperationKind.STAGEABLE,initial_state='old',intended_state='desired',current_state='old',terminal_phase=m.TerminalPhase.REJECTED_PRE_EFFECT,events=[m.Event(1,m.EventKind.EFFECT,'wrong')])
    def test_wrong_stageable_publication_fails_closed(self):
        m=self.mod
        with self.assertRaises(m.ContractError): m.reduce_outcome(operation_kind=m.OperationKind.STAGEABLE,initial_state='old',intended_state='desired',current_state='wrong',terminal_phase=m.TerminalPhase.EFFECT_COMMITTED,events=[m.Event(1,m.EventKind.EFFECT,'wrong')])

if __name__=='__main__': unittest.main()
