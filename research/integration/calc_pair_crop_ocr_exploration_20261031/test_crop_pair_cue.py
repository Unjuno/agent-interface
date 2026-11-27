import unittest
from crop_pair_cue import classify
H='level\tconf\ttext\n'
def t(text,confidence):return H+'5\t'+str(confidence)+'\t'+text+'\n'
class CropCueTests(unittest.TestCase):
 def test_correct_pair(self):self.assertEqual(classify(t('731',95),t('864',96)),'filled')
 def test_wrong_pair(self):self.assertEqual(classify(t('731',95),t('863',96)),'wrong')
 def test_missing_or_low_confidence_unknown(self):
  for a,b in ((H,t('864',96)),(t('731',89.9),t('864',96)),(t('731','nan'),t('864',96))):
   self.assertEqual(classify(a,b),'unknown')
 def test_multiple_tokens_unknown(self):self.assertEqual(classify(t('731',95)+'5\t95\t1\n',t('864',96)),'unknown')
 def test_invalid_tsv_unknown(self):self.assertEqual(classify('garbage',t('864',96)),'unknown')
