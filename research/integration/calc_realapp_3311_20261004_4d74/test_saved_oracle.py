import copy,json,pathlib,tempfile,unittest,xml.etree.ElementTree as E
from saved_oracle import N,score_saved,score_done
R=pathlib.Path(__file__).resolve().parent;D=R/'runs/cache03'
class SavedOracleTests(unittest.TestCase):
 def setUp(self):self.blob=(D/'cold.fods').read_bytes();self.raw=json.loads((D/'raw.json').read_text(encoding='utf-8'))['tasks'][0]
 def mutate(self,kind):
  tree=E.fromstring(self.blob);rows=tree.find('.//t:table',N).findall('t:table-row',N);cells=rows[1].findall('t:table-cell',N)
  if kind=='value':cells[2].set('{'+N['o']+'}value','999')
  if kind=='formula':cells[2].set('{'+N['t']+'}formula','of:=[.A2]+[.B2]')
  if kind=='header':rows[0].findall('t:table-cell',N)[0].find('p:p',N).text='wrong'
  if kind=='extra':
   c=E.SubElement(rows[1],'{'+N['t']+'}table-cell');c.set('{'+N['o']+'}value','9');E.SubElement(c,'{'+N['p']+'}p').text='9'
  return E.tostring(tree)
 def test_baseline(self):self.assertTrue(score_saved(self.blob,13,17)['pass_effect'])
 def test_value(self):self.assertFalse(score_saved(self.mutate('value'),13,17)['pass_effect'])
 def test_formula(self):self.assertFalse(score_saved(self.mutate('formula'),13,17)['pass_effect'])
 def test_header(self):self.assertFalse(score_saved(self.mutate('header'),13,17)['pass_effect'])
 def test_collateral(self):self.assertFalse(score_saved(self.mutate('extra'),13,17)['pass_effect'])
 def test_receipt_and_physical(self):
  row=copy.deepcopy(self.raw);row['physical']['keys']=[37];row['receipt']['status']='failed'
  self.assertGreaterEqual(len(score_done(D,row)['errors']),2)
if __name__=='__main__':unittest.main()
