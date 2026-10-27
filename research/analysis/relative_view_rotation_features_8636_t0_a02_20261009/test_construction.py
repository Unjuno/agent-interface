import unittest
import math
import candidate, runner, auditor


class ConstructionTests(unittest.TestCase):
    def test_spherical_frame_recovers_rotation_coordinates(self):
        ref,_=runner.render(0.0,0.0)
        cur,_=runner.render(0.17,-0.11)
        r=candidate.detect(96,96,cur.split(b"\n255\n",1)[1])
        t=candidate.detect(96,96,ref.split(b"\n255\n",1)[1])
        yaw,pitch,_,_=candidate.rotation_error(r,t)
        self.assertAlmostEqual(yaw,0.17,delta=.004)
        self.assertAlmostEqual(pitch,-0.11,delta=.004)

    def test_pairwise_spherical_distances_are_rotation_invariant(self):
        rows=[]
        for yaw,pitch in ((0,0),(.2,0),(0,-.2),(.13,-.09)):
            img,_=runner.render(yaw,pitch)
            p=candidate.detect(96,96,img.split(b"\n255\n",1)[1])
            _,b=candidate.frame(p)
            rows.append([round(candidate.dot(b[i],b[j]),5) for i,j in ((0,1),(0,2),(1,2))])
        for row in rows[1:]:
            for a,b in zip(rows[0],row): self.assertAlmostEqual(a,b,delta=.008)

    def test_focal_shape_change_and_invalid_generation_yield(self):
        ref,_=runner.render(0,0)
        shifted,_=runner.render(.1,.1,58)
        rp=candidate.detect(96,96,ref.split(b"\n255\n",1)[1])
        sp=candidate.detect(96,96,shifted.split(b"\n255\n",1)[1])
        with self.assertRaisesRegex(ValueError,"shape changed"):
            candidate.rotation_error(sp,rp)
        with self.assertRaisesRegex(ValueError,"stale target"):
            candidate.choose_action("spherical_features",rp,rp,{"width":96,"height":96,"target_generation":1,"viewport_generation":2})

    def test_near_singular_points_yield(self):
        img,_=runner.render(.1,.1,48,"near_singular")
        p=[(30.0,30.0),(30.5,30.5),(72.0,21.0)]
        with self.assertRaisesRegex(ValueError,"singular"):
            candidate.rotation_error(p,p)

    def test_identity_swap_fails_closed_for_both_image_arms(self):
        ref,_=runner.render(0,0); bad,_=runner.render(.1,.1,48,"swap_ids")
        rp=candidate.detect(96,96,ref.split(b"\n255\n",1)[1]); bp=candidate.detect(96,96,bad.split(b"\n255\n",1)[1])
        meta={"width":96,"height":96,"target_generation":1,"viewport_generation":1}
        for arm in ("raw_pixels","spherical_features"):
            with self.assertRaisesRegex(ValueError,"shape changed"):
                candidate.choose_action(arm,bp,rp,meta)

    def test_raw_fixed_linearization_is_finite_on_rotation_fixture(self):
        ref,_=runner.render(0,0); cur,_=runner.render(.12,-.08)
        rp=candidate.detect(96,96,ref.split(b"\n255\n",1)[1]); cp=candidate.detect(96,96,cur.split(b"\n255\n",1)[1])
        y,p=candidate.raw_error(cp,rp)
        self.assertTrue(math.isfinite(y) and math.isfinite(p))
        self.assertAlmostEqual(y,.12,delta=.03)
        self.assertAlmostEqual(p,-.08,delta=.03)

    def test_independent_audit_rejects_stale_generation_and_missing_release(self):
        auditor.check_generation({"target_generation":3,"viewport_generation":3})
        with self.assertRaisesRegex(ValueError,"stale"):
            auditor.check_generation({"target_generation":3,"viewport_generation":4})
        observations=[{"trial":"t","step":0,"event_type":"OBSERVATION","status":"STOP"},
                      {"trial":"t","step":1,"event_type":"RELEASE","status":"RELEASE","action":[0.0,0.0],"release_verified":True}]
        auditor.check_order(observations); auditor.check_release(observations)
        with self.assertRaisesRegex(ValueError,"release"):
            auditor.check_release(observations[:1])

    def test_stress_renderers_match_independent_reconstruction(self):
        for fault,width,height in (("hide_second",96,96),("low_texture",96,96),
                                   ("camera_translation",96,96),("range_variation",96,96),
                                   ("stale_frame",96,96),("viewport_resize",112,112)):
            image,_=runner.render(.08,-.04,48.0,fault,width,height)
            expected,_=auditor.expected_renderer(.08,-.04,48.0,fault,width,height)
            self.assertEqual(image,expected,fault)

    def test_radial_range_is_projection_null_and_stress_schedule_is_balanced(self):
        normal,_=runner.render(.08,-.04,48.0)
        varied,_=runner.render(.08,-.04,48.0,"range_variation")
        self.assertEqual(normal,varied)
        counts={fault:0 for fault in ("hide_second","swap_ids","move_third","near_singular","low_texture","camera_translation","stale_frame","viewport_resize","range_variation")}
        for seed in runner.SEEDS:
            *_,fault=runner.scenario(seed,"feature_loss")
            counts[fault]+=1
        self.assertEqual(sorted(counts.values()),[3,3,3,3,3,3,4,4,4])

    def test_explicit_invalid_faults_require_image_arm_abstention(self):
        self.assertTrue(all(auditor.expected_fault_yield(fault) for fault in
                            ("hide_second","swap_ids","move_third","near_singular","low_texture","camera_translation","stale_frame","viewport_resize")))
        self.assertFalse(auditor.expected_fault_yield("range_variation"))


    def test_focal_shift_shape_guard_is_separate_stress_yield(self):
        seed=30011  # retained A01 first-audit counterexample; construction regression only
        yaw,pitch,focal,fault=runner.scenario(seed,"focal_shift")
        self.assertIsNone(fault)
        ref,_=runner.render(0,0,48)
        frame,_=runner.render(yaw,pitch,focal)
        ref_points=candidate.detect(96,96,ref.split(b"\n255\n",1)[1])
        current=candidate.detect(96,96,frame.split(b"\n255\n",1)[1])
        meta={"width":96,"height":96,"target_generation":seed,"viewport_generation":seed}
        for arm in ("raw_pixels","spherical_features"):
            expected,reason=auditor.expected_stress_yield("focal_shift",arm,current,ref_points,meta)
            self.assertTrue(expected)
            self.assertEqual(reason,"shape changed")
            with self.assertRaisesRegex(ValueError,"shape changed"):
                candidate.choose_action(arm,current,ref_points,meta)


if __name__=="__main__": unittest.main()
