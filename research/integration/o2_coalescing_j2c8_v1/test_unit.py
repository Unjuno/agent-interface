import copy
import unittest
from actor import produce, consume
from fixtures import make
from audit import advance


class CompositionTests(unittest.TestCase):
    def test_single_all_modes(self):
        for mode in ('FIFO','ENCODE_THEN_SELECT','SELECT_THEN_ENCODE'):
            p=produce(make('SINGLE','unit',mode,True))
            c=consume({'messages':p['messages']})
            self.assertTrue(all(v['accepted'] for v in c['observations']))

    def test_negative_retains_bootstrap(self):
        p=produce(make('CHANGE_BURST','unit','ENCODE_THEN_SELECT',True))
        c=consume({'messages':p['messages']})
        self.assertFalse(c['observations'][-1]['accepted'])
        self.assertEqual(c['observations'][-1]['before'],c['observations'][-1]['after'])

    def test_selection_and_input_nonmutation(self):
        x=make('CHANGE_BURST','unit','SELECT_THEN_ENCODE',True); old=copy.deepcopy(x)
        p=produce(x)
        self.assertEqual(x,old)
        self.assertEqual(len(p['encoded']),2)
        self.assertEqual(p['selection']['coalesced_count'],2)

    def test_critical_records(self):
        p=produce(make('CRITICAL_BURST','unit','SELECT_THEN_ENCODE',True))
        c=consume({'messages':p['messages']})
        self.assertEqual([r['kind'] for r in c['critical']],['FOCUS_CHANGED','EFFECT_VERIFIED'])
        self.assertFalse(p['continuous_visual_coverage'])

    def test_equal_pixels_not_equal_observation(self):
        p=produce(make('ABA_BURST','unit','ENCODE_THEN_SELECT',True))
        c=consume({'messages':p['messages']})
        self.assertFalse(c['observations'][-1]['accepted'])
        p=produce(make('ABA_BURST','unit','SELECT_THEN_ENCODE',True))
        c=consume({'messages':p['messages']})
        self.assertTrue(c['observations'][-1]['accepted'])

    def test_separate_streams(self):
        p=produce(make('TWO_STREAMS','unit','SELECT_THEN_ENCODE',True))
        c=consume({'messages':p['messages']})
        self.assertEqual(len(c['final']),2)
        self.assertTrue(all(s['sequence']==2 for s in c['final'].values()))

    def test_independent_decoder(self):
        p=produce(make('CHANGE_BURST','unit','FIFO',True)); states={}
        for m in p['messages']:
            key=m['scope']; old=states.get(key,{'sequence':0,'metadata':None,'pixels':None})
            ok,states[key]=advance(old,key,m['wire']); self.assertTrue(ok)
        self.assertEqual(states,consume({'messages':p['messages']})['final'])

    def test_authority_neutral(self):
        p=produce(make('UNCHANGED_BURST','unit','SELECT_THEN_ENCODE',True))
        c=consume({'messages':p['messages']})
        self.assertFalse(p['input_authority']); self.assertFalse(c['input_authority'])
        self.assertIsNone(c['task_success'])


if __name__=='__main__': unittest.main()
