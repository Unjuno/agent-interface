import unittest
from cell_cue import cell_pair_cue
HEADER='left\ttop\twidth\theight\tconf\ttext\n'
def tsv(a='731',b='864',conf='95',extra=''):
 return HEADER+f'92\t185\t22\t12\t{conf}\t{a}\n92\t205\t22\t12\t95\t{b}\n'+extra
class CueTests(unittest.TestCase):
 def cue(self,text,**kwargs):return cell_pair_cue(text,main_sheet_reviewed=kwargs.get('review',True),modal_present=kwargs.get('modal',False))
 def test_exact(self):self.assertEqual(self.cue(tsv()),'filled')
 def test_wrong_digit_is_not_success(self):self.assertEqual(self.cue(tsv('713')),'wrong')
 def test_missing_value_is_unknown(self):self.assertEqual(self.cue(tsv(b='')),'unknown')
 def test_duplicate_value_is_unknown(self):self.assertEqual(self.cue(tsv(extra='93\t185\t22\t12\t95\t731\n')),'unknown')
 def test_formula_bar_value_is_not_cell(self):self.assertEqual(self.cue(HEADER+'92\t100\t22\t12\t95\t731\n92\t205\t22\t12\t95\t864\n'),'unknown')
 def test_low_confidence_or_non_digit_is_unknown(self):
  for s in [tsv(conf='89'),tsv('73l'),tsv(conf='nan'),tsv(conf='inf')]:self.assertEqual(self.cue(s),'unknown')
 def test_modal_or_unreviewed_sheet_never_certifies(self):
  self.assertEqual(self.cue(tsv(),modal=True),'unknown');self.assertEqual(self.cue(tsv(),review=False),'unknown')
 def test_malformed_or_changed_layout_unknown(self):
  for s in [tsv().replace('185','285'),tsv().replace('92','bad'),HEADER,'not tsv']:
   self.assertEqual(self.cue(s),'unknown')
if __name__=='__main__':unittest.main()
