import unittest
from model import Policy, decide

class Tests(unittest.TestCase):
    def test_blind(self): self.assertEqual(decide(Policy.BLIND_FULL,'abc',2,'ab').text,'abc')
    def test_sender(self): self.assertEqual(decide(Policy.SENDER_SUFFIX,'abc',2,'a').text,'c')
    def test_observed_prefix(self): self.assertEqual(decide(Policy.OBSERVED_PREFIX,'abc',2,'a').text,'bc')
    def test_observed_complete(self): self.assertEqual(decide(Policy.OBSERVED_PREFIX,'abc',3,'abc').text,'')
    def test_observed_nonprefix_refuses(self): self.assertFalse(decide(Policy.OBSERVED_PREFIX,'abc',2,'ac').accepted)
    def test_sent_count_validation(self):
        with self.assertRaises(ValueError): decide(Policy.SENDER_SUFFIX,'abc',4,'abc')

if __name__=='__main__': unittest.main()
