import copy
import unittest
from pathlib import Path
from probe import collected, observer_args

class Probe(unittest.TestCase):
    def test_collection_requires_all_three_exact_terminal_exits(self):
        good={'status':'COLLECTED_SOURCE_DIAGNOSTIC','lifecycle':{'fixture_exit':0,'observer_exit':0,'xvfb_exit':0}}
        self.assertTrue(collected(good))
        for value in (1,False,None):
            bad=copy.deepcopy(good); bad['lifecycle']['observer_exit']=value
            self.assertFalse(collected(bad))
    def test_observer_has_required_epoch_file(self):
        args=observer_args(Path('/out/result'),42)
        self.assertIn('--epoch-file',args)
        self.assertEqual(args[args.index('--epoch-file')+1],'/out/result/epoch.json')
        self.assertEqual(args[args.index('--window')+1],'42')

if __name__=='__main__': unittest.main()
