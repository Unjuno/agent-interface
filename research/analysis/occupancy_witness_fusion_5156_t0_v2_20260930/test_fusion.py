import unittest

from fusion import fuse


def record(down=(0, 1), up=(3, 4), start=1, returned=2, sync=3):
    identity = {
        "owner_id": "owner-1",
        "actuation_id": "act-1",
        "keycode": 38,
        "display_id": "display-1",
        "clock_id": "mono-ns-1",
    }
    return {
        "identity": identity,
        "down_query": {**identity, "query": list(down)},
        "up_query": {**identity, "query": list(up)},
        "owner_release": {
            **identity,
            "request_start": start,
            "request_return": returned,
            "sync_return": sync,
            "release_count": 1,
            "repress_count": 0,
        },
    }


class FusionTests(unittest.TestCase):
    def test_intersection_tightens_both_sources(self):
        self.assertEqual(
            fuse(record(down=(0, 2), up=(3, 8), start=4, returned=5, sync=6)),
            {"decision": "BOUNDED", "lower_open": 4, "upper_closed": 6, "authority": False},
        )

    def test_empty_intersection_is_unknown(self):
        self.assertEqual(fuse(record(down=(0, 2), up=(3, 4), start=5, returned=6, sync=7))["decision"], "UNKNOWN")

    def test_identity_mismatch_is_unknown(self):
        row = record()
        row["up_query"]["display_id"] = "other-display"
        self.assertEqual(fuse(row)["reason"], "IDENTITY_MISMATCH")

    def test_duplicate_release_is_unknown(self):
        row = record()
        row["owner_release"]["release_count"] = 2
        self.assertEqual(fuse(row)["reason"], "NON_SINGLE_TRANSITION")

    def test_repress_is_unknown(self):
        row = record()
        row["owner_release"]["repress_count"] = 1
        self.assertEqual(fuse(row)["reason"], "NON_SINGLE_TRANSITION")

    def test_boolean_timestamp_is_not_an_integer_time(self):
        row = record()
        row["owner_release"]["request_start"] = True
        self.assertEqual(fuse(row)["decision"], "UNKNOWN")

    def test_inverted_owner_order_is_unknown(self):
        self.assertEqual(fuse(record(start=3, returned=2, sync=4))["reason"], "INVALID_OWNER_ORDER")

    def test_authority_is_always_false(self):
        self.assertIs(fuse(record())["authority"], False)

    def test_both_sources_can_strictly_narrow_the_interval(self):
        result = fuse(record(down=(1, 2), up=(5, 6), start=4, returned=5, sync=8))
        self.assertEqual(result["lower_open"], 4)
        self.assertEqual(result["upper_closed"], 6)
        self.assertLess(6 - 4, 6 - 1)
        self.assertLess(6 - 4, 8 - 4)

    def test_boolean_release_count_is_malformed(self):
        row = record()
        row["owner_release"]["release_count"] = True
        self.assertEqual(fuse(row)["decision"], "UNKNOWN")

    def test_malformed_shared_identity_is_unknown(self):
        row = record()
        row["identity"]["keycode"] = True
        for source in (row["down_query"], row["up_query"], row["owner_release"]):
            source["keycode"] = True
        self.assertEqual(fuse(row)["decision"], "UNKNOWN")

    def test_boolean_source_keycode_is_unknown(self):
        row = record()
        row["identity"]["keycode"] = 1
        for source in (row["down_query"], row["up_query"], row["owner_release"]):
            source["keycode"] = 1
        row["up_query"]["keycode"] = True
        self.assertEqual(fuse(row)["decision"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
