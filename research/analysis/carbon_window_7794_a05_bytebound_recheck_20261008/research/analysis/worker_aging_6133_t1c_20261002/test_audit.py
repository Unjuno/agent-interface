import unittest

from audit import independently_detect


def rows(rss, latency):
    return [{"generation_before": 1, "age_before": i, "rss_mb": r, "latency_ms": t}
            for i, (r, t) in enumerate(zip(rss, latency))]


class DetectorTests(unittest.TestCase):
    def test_joint_leak_detected(self):
        self.assertTrue(independently_detect(rows([100, 102, 104, 106, 108], [20, 21, 22, 23, 24])))

    def test_cache_only_not_aging(self):
        self.assertFalse(independently_detect(rows([100, 103, 106, 109, 112], [20, 20, 20, 20, 20])))

    def test_thermal_only_not_aging(self):
        self.assertFalse(independently_detect(rows([100, 100, 100, 100, 100], [20, 21, 22, 23, 24])))

    def test_short_span_not_aging(self):
        self.assertFalse(independently_detect(rows([100, 108], [20, 24])))


if __name__ == "__main__":
    unittest.main()
