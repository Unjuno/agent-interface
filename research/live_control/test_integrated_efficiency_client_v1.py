import os
import unittest
from unittest.mock import patch

from source_pixel_transform_v1 import to_window_content


class ChromiumConfigurationTests(unittest.TestCase):
    def test_configured_executable_is_forwarded_without_shell(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        with patch.dict(os.environ, {"AGENT_INTERFACE_CHROMIUM": "/usr/bin/chromium"}):
            command = RuntimeClient("out", 7)._runtime_command()
        self.assertEqual(command[-2:], ["--chromium", "/usr/bin/chromium"])
        self.assertIn("--app", command)

    def test_unset_override_preserves_existing_default(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        with patch.dict(os.environ, {}, clear=True):
            command = RuntimeClient("out", 7)._runtime_command()
        self.assertNotIn("--chromium", command)

    def test_empty_override_is_rejected(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        with patch.dict(os.environ, {"AGENT_INTERFACE_CHROMIUM": ""}):
            with self.assertRaises(ValueError):
                RuntimeClient("out", 7)


class MintPointTransformTests(unittest.TestCase):
    def test_source_pixels_are_rebased_to_window_content_origin(self):
        source = {"sequence": 6, "pointer_binding": {"geometry": [10, 10, 1050, 780]}}
        grounding = {"field_point": [234, 402], "submit_point": [386, 402]}
        self.assertEqual(to_window_content(grounding["field_point"],
                                          source["pointer_binding"]["geometry"]),
                         [224, 392])
        self.assertEqual(to_window_content(grounding["submit_point"],
                                          source["pointer_binding"]["geometry"]),
                         [376, 392])

class MintAbsolutePointTests(unittest.TestCase):
    def test_mint_uses_observation_pixels_even_with_nonzero_window_origin(self):
        from integrated_efficiency_client_v1 import RuntimeClient
        client = RuntimeClient.__new__(RuntimeClient)
        calls = []
        def capture(_label, steps):
            calls.extend(steps)
            return {"terminal": {"status": "completed"}, "point_mints": [{}]}
        client.submit = capture
        aliases, refusal = client.mint("A", {"sequence": 9, "pointer_binding": {"geometry": [10, 10, 1050, 780]}}, {"field_point": [226, 401], "submit_point": [376, 401]}, "test")
        self.assertIsNone(refusal)
        self.assertEqual([s["point"] for s in calls], [[226, 401], [376, 401]])
        self.assertEqual([s["coordinate_frame"] for s in calls], ["window_content", "window_content"])


if __name__ == "__main__":
    unittest.main()
