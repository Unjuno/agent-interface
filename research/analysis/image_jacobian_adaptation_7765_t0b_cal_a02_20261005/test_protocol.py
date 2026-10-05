import unittest
from audit_calibration import plant


class ProtocolTests(unittest.TestCase):
    def test_cross_coupling_rng_consumption_matches_frozen_generator(self):
        from calibrate import runner, P
        for seed in range(3000, 3020):
            self.assertEqual(plant(seed, "cross_coupling"), runner.plant(seed, "cross_coupling"))


if __name__ == "__main__": unittest.main()
