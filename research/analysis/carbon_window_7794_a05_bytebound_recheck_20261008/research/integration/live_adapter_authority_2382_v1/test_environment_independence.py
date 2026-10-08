import os
import unittest

from validate_receipt import validate


class EnvironmentIndependenceTests(unittest.TestCase):
    def test_environment_presence_does_not_change_invalid_receipt(self):
        previous = os.environ.get("AGENT_INTERFACE_LIVE_AUTHORITY")
        try:
            os.environ["AGENT_INTERFACE_LIVE_AUTHORITY"] = "true"
            self.assertEqual(validate(None), (False, "RECEIPT_NOT_OBJECT"))
            self.assertEqual(validate({"status": "DECLARED"}), (False, "RECEIPT_FIELDS_MISMATCH"))
        finally:
            if previous is None:
                os.environ.pop("AGENT_INTERFACE_LIVE_AUTHORITY", None)
            else:
                os.environ["AGENT_INTERFACE_LIVE_AUTHORITY"] = previous


if __name__ == "__main__":
    unittest.main()
