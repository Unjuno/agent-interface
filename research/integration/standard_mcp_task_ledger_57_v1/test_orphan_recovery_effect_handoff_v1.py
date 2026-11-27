from pathlib import Path
import copy, json, unittest
from orphan_recovery_effect_handoff_v1 import adapt_orphan_recovery_effect, OrphanRecoveryHandoffError

ROOT=Path(__file__).resolve().parents[3]
PACKET=ROOT/'research/integration/win32_expired_authority_delayed_effect_r24_20261123'
RAW=PACKET/'raw'
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))

class OrphanRecoveryEffectHandoffR24Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.measured=read(RAW/'offline-reconstruction-r04/measured-run.json')
        cls.action=read(RAW/'interface_results-047e67d737ef4b889413a560669cf219.json')
        cls.action=json.loads(cls.action['result']['content'][0]['text'])
        cls.recovery=read(RAW/'orphan-recovery-api-attempt.json')
        cls.recovery_raw=read(RAW/'recovery-mcp'/cls.recovery['initial_recovery_receipt']['call_id']/'report.json')
        cls.effect=read(RAW/'recorder/effect-score-r24-offline.json')
        cls.custody=cls.recovery['custody_record']
    def adapt(self, **changes):
        args={'measured':copy.deepcopy(self.measured),'action_public':copy.deepcopy(self.action),
              'recovery_envelope':copy.deepcopy(self.recovery),'recovery_raw_report':copy.deepcopy(self.recovery_raw),
              'effect_receipt':copy.deepcopy(self.effect),
              'custody_record':copy.deepcopy(self.custody)}
        args.update(changes)
        return adapt_orphan_recovery_effect(**args)
    def test_joins_separate_recovery_without_upgrading_unknown_action(self):
        result=self.adapt()
        self.assertEqual(result['source_action']['status'],'unknown')
        self.assertFalse(result['source_action']['release_confirmed'])
        self.assertIsNone(result['source_action']['task_success'])
        self.assertFalse(result['source_action']['replay_allowed'])
        self.assertEqual(result['recovery_attempt']['status'],'recovered')
        self.assertTrue(result['recovery_attempt']['release_confirmed'])
        self.assertTrue(result['effect']['factual_task_success'])
        self.assertEqual(result['effect']['effect_timing'],'after_authority_before_release')
        self.assertFalse(result['effect']['eligible_task_success'])
    def test_rejects_source_action_promotion(self):
        action=copy.deepcopy(self.action); action['action']['status']='completed'
        with self.assertRaises(OrphanRecoveryHandoffError): self.adapt(action_public=action)
    def test_rejects_recovery_for_different_generation(self):
        recovery=copy.deepcopy(self.recovery); recovery['initial_recovery_receipt']['source_target_generation']='0'*64
        with self.assertRaises(OrphanRecoveryHandoffError): self.adapt(recovery_envelope=recovery)
    def test_rejects_missing_horizon(self):
        recovery=copy.deepcopy(self.recovery); recovery['initial_recovery_receipt']['recovery_receipt']['late_input_horizon_verified']=False
        with self.assertRaises(OrphanRecoveryHandoffError): self.adapt(recovery_envelope=recovery)
    def test_rejects_unmatched_public_recovery_report(self):
        raw=copy.deepcopy(self.recovery_raw); raw['source_target_generation']='0'*64
        with self.assertRaises(OrphanRecoveryHandoffError): self.adapt(recovery_raw_report=raw)
    def test_rejects_modified_custody_record(self):
        custody=copy.deepcopy(self.custody); custody['obligations']=['key:fixture:B:virtual_key']
        with self.assertRaises(OrphanRecoveryHandoffError): self.adapt(custody_record=custody)
    def test_rejects_attribution_from_another_release(self):
        measured=copy.deepcopy(self.measured); measured['measurement']['effect_attribution']['release_received_ns']+=1
        with self.assertRaises(OrphanRecoveryHandoffError): self.adapt(measured=measured)

if __name__=='__main__': unittest.main(verbosity=2)
