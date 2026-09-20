import unittest
from unittest.mock import patch, MagicMock

from readiness import resolve_candidates, require_window
from formal_session import geom, launch


class ReadinessTests(unittest.TestCase):
    def test_exact_role_identity_is_admitted(self):
        rows = [{"window": "42", "raw": 'WM_NAME(STRING) = "Untitled 1 - LibreOffice Calc"'}]
        self.assertEqual(resolve_candidates("calc", rows)["status"], "READY")
        self.assertEqual(require_window("calc", rows), "42")

    def test_preregistered_role_filters(self):
        cases = (
            ("inkscape", 'WM_NAME(STRING) = "Inkscape 1.2.2"'),
            ("calc", 'WM_NAME(STRING) = "Untitled 1 - LibreOffice Calc"'),
            ("chromium", 'WM_CLASS(STRING) = "chromium (/tmp/profile)", "Chromium"'),
        )
        for role, raw in cases:
            with self.subTest(role=role):
                self.assertEqual(resolve_candidates(role, [{"window":"7","raw":raw}])["status"], "READY")

    def test_missing_identity_stops(self):
        result = resolve_candidates("calc", [{"window": "42", "raw": 'WM_NAME(STRING) = "Tip of the Day"'}])
        self.assertEqual(result["status"], "STOP_IDENTITY_MISSING")
        with self.assertRaisesRegex(RuntimeError, "STOP_IDENTITY_MISSING"):
            require_window("calc", [])

    def test_ambiguous_identity_stops(self):
        rows = [{"window": str(i), "raw": 'WM_NAME(STRING) = "Untitled 1 - LibreOffice Calc"'} for i in (42, 43)]
        self.assertEqual(resolve_candidates("calc", rows)["status"], "STOP_IDENTITY_AMBIGUOUS")
        with self.assertRaisesRegex(RuntimeError, "STOP_IDENTITY_AMBIGUOUS"):
            require_window("calc", rows)

    def test_none_window_is_rejected_before_geometry_tool_call(self):
        with self.assertRaisesRegex(RuntimeError, "STOP_IDENTITY_MISSING"):
            geom({}, None)

    def test_missing_launch_stops_before_geometry_and_cleans_owner(self):
        proc=MagicMock(); proc.pid=424242
        with patch("formal_session.windows", return_value=[]), \
             patch("formal_session.subprocess.Popen", return_value=proc), \
             patch("formal_session.stop_process_group", return_value={"pid":424242,"returncode":-15,"remaining_pids":[]}) as cleanup, \
             patch("formal_session.wait_role_window", side_effect=RuntimeError("STOP_IDENTITY_MISSING:calc")), \
             patch("formal_session.geom") as geometry:
            with self.assertRaisesRegex(RuntimeError,"STOP_IDENTITY_MISSING"):
                launch(["libreoffice"],{},"calc")
        geometry.assert_not_called()
        cleanup.assert_called_once_with(proc)

    def test_ambiguous_readiness_stops_before_geometry(self):
        proc=MagicMock(); proc.pid=424242
        with patch("formal_session.windows", return_value=[]), \
             patch("formal_session.subprocess.Popen", return_value=proc), \
             patch("formal_session.stop_process_group", return_value={"pid":424242,"returncode":-15,"remaining_pids":[]}) as cleanup, \
             patch("formal_session.wait_role_window", side_effect=RuntimeError("STOP_IDENTITY_AMBIGUOUS:calc")), \
             patch("formal_session.geom") as geometry:
            with self.assertRaisesRegex(RuntimeError,"STOP_IDENTITY_AMBIGUOUS"):
                launch(["libreoffice"],{},"calc")
        geometry.assert_not_called()
        cleanup.assert_called_once_with(proc)


if __name__ == "__main__":
    unittest.main()
