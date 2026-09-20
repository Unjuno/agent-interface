import unittest
import torch
import runner


class Pilot07ConstructionTests(unittest.TestCase):
    def test_eval_generators_are_deterministic(self):
        self.assertEqual(runner.shifted_class(1,16,789).tolist(),runner.shifted_class(1,16,789).tolist())

    def test_training_data_size_and_mixture(self):
        control,_=runner.training_rows(3470,False)
        augmented,_=runner.training_rows(3470,True)
        self.assertEqual(list(control.shape),[6144,6])
        self.assertEqual(list(augmented.shape),[6144,6])
        self.assertTrue(torch.equal(control[:2048],augmented[:2048]))
        self.assertTrue(torch.equal(control[4096:],augmented[4096:]))
        for dx,dy,vx,vy,conf,visible in augmented[2048+1024:4096].tolist():
            self.assertTrue(.071<=abs(dx)<=.149)
            self.assertLessEqual(abs(dy),.10)
            self.assertLessEqual(abs(vx),.05); self.assertLessEqual(abs(vy),.05)
            self.assertTrue(.80<=conf<=1.); self.assertEqual(visible,1.)

    def test_eval_seeds_are_disjoint_from_training_seed_map(self):
        train={s+10+c for s in runner.SEEDS for c in range(3)}|{s+40 for s in runner.SEEDS}
        evals={s+offset+c for s in runner.SEEDS for offset in (100,200) for c in range(3)}|{s+300 for s in runner.SEEDS}
        self.assertFalse(train & evals)

    def test_boundary_and_invalid_counts(self):
        self.assertEqual(len(runner.boundary_rows()),1536)
        self.assertEqual(len(runner.invalid_inputs()),5)

    def test_paired_minibatch_stream_is_fixed(self):
        a=runner.minibatch_stream(3470); b=runner.minibatch_stream(3470)
        self.assertEqual(runner.canonical_hash([x.tolist() for x in a]),runner.canonical_hash([x.tolist() for x in b]))
        self.assertEqual(len(a),700)
        self.assertTrue(all(list(x.shape)==[64] for x in a))


if __name__=="__main__": unittest.main(verbosity=2)
