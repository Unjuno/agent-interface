import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXP=ROOT/'experiment.py'; AUD=ROOT/'audit.py'
class T(unittest.TestCase):
  def runone(self,scenario):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); plan=t/'p.json'; out=t/'o'; plan.write_text(json.dumps({'cases':[{'id':'x','scenario':scenario}]}))
      subprocess.run([sys.executable,str(EXP),str(plan),str(out)],check=True)
      r=json.loads((out/'x'/'result.json').read_text()); a=json.loads(subprocess.check_output([sys.executable,str(AUD),str(out)],text=True)); return r,a
  def test_correct(self):
    r,a=self.runone('correct'); self.assertEqual(r['phase_result'],'EFFECT_VERIFIED'); self.assertTrue(a['all_pass'])
  def test_compensated_preserves_history(self):
    r,a=self.runone('wrong_compensated'); self.assertEqual(r['final'],'old'); self.assertEqual([e['value'] for e in r['events']],['wrong','old']); self.assertEqual(r['phase_result'],'EFFECT_CONTRADICTED_COMPENSATED')
  def test_final_state_only_is_false_history_claim(self):
    r,a=self.runone('wrong_compensated'); self.assertEqual(r['final_state_only_result'],'NO_EFFECT'); self.assertEqual(a['final_only_truthful_count'],0)
  def test_uncompensated(self):
    r,a=self.runone('wrong_uncompensated'); self.assertEqual(r['final'],'wrong'); self.assertEqual(r['phase_result'],'EFFECT_CONTRADICTED_UNCOMPENSATED')
  def test_wrong_first_effect_retained(self):
    r,a=self.runone('wrong_compensated'); self.assertEqual(r['events'][0]['kind'],'effect'); self.assertEqual(r['events'][0]['value'],'wrong')
if __name__=='__main__': unittest.main()
