import unittest
import numpy as np
from shadow_patch_match_v1 import search

class ShadowSearchTests(unittest.TestCase):
    def test_shifted_unique_patch_finds_candidate_without_authority(self):
        rng=np.random.default_rng(901)
        source=rng.integers(0,256,(64,80,3),dtype=np.uint8)
        checked=rng.integers(0,256,(64,80,3),dtype=np.uint8)
        checked[24:40,38:54]=source[24:40,24:40]
        result=search(source,checked,(32,32))
        self.assertIsNotNone(result)
        self.assertEqual(result['candidate'],(46,32))
        self.assertEqual(result['best_sum'],0)
        self.assertFalse(result['authority_granted'])
        self.assertTrue(result['requires_revalidation'])

    def test_edge_clipping_and_signed_differences_match_scalar_reference(self):
        rng=np.random.default_rng(27)
        for height,width,origin in ((16,16,(8,8)),(40,56,(8,8)),(40,56,(48,32)),(55,71,(35,27))):
            source=rng.integers(0,256,(height,width,3),dtype=np.uint8)
            checked=rng.integers(0,256,(height,width,3),dtype=np.uint8)
            x,y=origin;template=source[y-8:y+8,x-8:x+8].astype(np.int16);rows=[]
            for dy in range(-60,61,2):
                for dx in range(-80,81,2):
                    if 8<=x+dx<=width-8 and 8<=y+dy<=height-8:
                        patch=checked[y+dy-8:y+dy+8,x+dx-8:x+dx+8].astype(np.int16)
                        rows.append((int(np.abs(template-patch).sum()),dx,dy))
            rows.sort();best=rows[0];runner=next((q for q in rows[1:] if abs(q[1]-best[1])>16 or abs(q[2]-best[2])>16),None)
            result=search(source,checked,origin)
            self.assertEqual(result['candidate'],(x+best[1],y+best[2]))
            self.assertEqual(result['best_sum'],best[0])
            self.assertEqual(result['runner_sum'],None if runner is None else runner[0])
            self.assertEqual(result['candidate_count'],len(rows))

    def test_duplicate_matches_report_zero_gap_instead_of_identity(self):
        rng=np.random.default_rng(38);source=rng.integers(0,256,(64,96,3),dtype=np.uint8)
        checked=rng.integers(0,256,(64,96,3),dtype=np.uint8)
        patch=source[24:40,24:40];checked[24:40,8:24]=patch;checked[24:40,56:72]=patch
        result=search(source,checked,(32,32))
        self.assertEqual(result['best_sum'],0)
        self.assertEqual(result['runner_sum'],0)
        self.assertFalse(result['authority_granted'])
        self.assertTrue(result['requires_revalidation'])

    def test_malformed_images_and_out_of_bounds_origin_are_rejected(self):
        image=np.zeros((32,32,3),dtype=np.uint8)
        for source,checked,origin in ((image,image,(7,8)),(image,image,(8,25)),(image,image,(True,8)),(image,image.astype(np.int16),(8,8)),(image,image[:,:,:2],(8,8))):
            with self.subTest(origin=origin,shape=checked.shape,dtype=checked.dtype):
                with self.assertRaises(ValueError):search(source,checked,origin)

if __name__=='__main__':unittest.main()
