import json
import unittest


class FramingConstructionTests(unittest.TestCase):
    def test_removing_only_lf_preserves_json_but_breaks_jsonl(self):
        complete = b'{"result":{"status":"completed"}}\n'
        delivered = complete[:-1]
        self.assertEqual(json.loads(delivered)["result"]["status"], "completed")
        self.assertTrue(complete.endswith(b"\n"))
        self.assertFalse(delivered.endswith(b"\n"))
        self.assertEqual(delivered, complete[:-1])

    def test_shorter_prefix_is_invalid_json_control(self):
        complete = b'{"result":{"status":"completed"}}\n'
        with self.assertRaises(json.JSONDecodeError):
            json.loads(complete[: len(complete) // 2])


if __name__ == "__main__":
    unittest.main()
