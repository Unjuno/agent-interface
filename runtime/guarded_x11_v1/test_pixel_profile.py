"""Constrained, data-only pixel predicates for the guarded compiled caller."""
import copy
import unittest
from PIL import Image

from runtime.guarded_x11_v1.pixel_profile import build_callbacks
from runtime.core_v1.test_compiled_gui import interface


class PixelProfileTests(unittest.TestCase):
    def setup_profile(self):
        spec = interface()
        spec['predicates'].append('present')
        return spec, {
            'phase': {'point':[1,1], 'states':[
                {'rgb':[0,0,0], 'value':0},
                {'rgb':[1,2,3], 'value':1}]},
            'present': {'point':[2,2], 'states':[{'rgb':[9,8,7], 'value':True}]},
        }, {
            'enter': {'point':[3,3], 'rgb':[4,5,6]},
            'save': {'point':[4,4], 'rgb':[7,8,9]},
        }

    def test_callbacks_decode_only_declared_exact_rgb_states(self):
        spec, predicates, effects = self.setup_profile()
        perceive, verify = build_callbacks(spec, predicates, effects)
        image = Image.new('RGB',(8,8),(255,255,255))
        image.putpixel((1,1),(1,2,3)); image.putpixel((2,2),(9,8,7))
        native = {'sequence':1}
        before = copy.deepcopy(native)
        self.assertEqual(perceive(native,image), {'phase':1,'present':True})
        self.assertEqual(native,before)
        self.assertEqual(perceive(native,Image.new('RGB',(8,8),(0,0,0))),
                         {'phase':0,'present':'unknown'})
        result = verify({'action':'enter','observation':{'evidence_ref':'obs-1'}},
                        native,image)
        self.assertEqual(result,{'status':'unavailable','evidence_ref':'obs-1'})
        image.putpixel((3,3),(4,5,6))
        self.assertEqual(verify({'action':'enter','observation':{'evidence_ref':'obs-1'}},
                                native,image),
                         {'status':'succeeded','evidence_ref':'obs-1'})

    def test_profile_must_cover_exact_predicates_and_actions(self):
        spec, predicates, effects = self.setup_profile()
        with self.assertRaisesRegex(ValueError,'predicate'):
            build_callbacks(spec, {'phase':predicates['phase']}, effects)
        with self.assertRaisesRegex(ValueError,'action'):
            build_callbacks(spec, predicates, {'enter':effects['enter']})

    def test_invalid_or_duplicate_pixel_values_are_rejected(self):
        spec, predicates, effects = self.setup_profile()
        for rule in (
            {'point':[True,1], 'states':[{'rgb':[0,0,0],'value':0}]},
            {'point':[1,1], 'states':[{'rgb':[256,0,0],'value':0}]},
            {'point':[1,1], 'states':[{'rgb':[0,0,0],'value':False},
                                      {'rgb':[0,0,0],'value':0}]},
        ):
            with self.subTest(rule=rule):
                with self.assertRaises(ValueError):
                    build_callbacks(spec, {'phase':rule,'present':predicates['present']}, effects)


if __name__ == '__main__':
    unittest.main()
