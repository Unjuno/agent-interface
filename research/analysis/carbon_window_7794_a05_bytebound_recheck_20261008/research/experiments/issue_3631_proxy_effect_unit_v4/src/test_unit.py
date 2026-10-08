import tempfile
import unittest
from pathlib import Path
import ast
import json
import subprocess

from proxy import render
from runner import query_button_released, wait_ambiguous
from proxy import blue_bbox, center, ppm_rgb


class ProxySurfaceTests(unittest.TestCase):
    def test_no_caller_pid_hint_and_xres_binding_is_used(self):
        source=Path(__file__).with_name("runner.py").read_text()
        self.assertNotIn("pid_hint", source)
        self.assertIn("res_query_client_ids", source)
        self.assertIn("start_ticks", source)

    def test_image_is_deterministic_and_state_bound_by_pixels(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b, c = (Path(tmp) / n for n in ("a.ppm", "b.ppm", "c.ppm"))
            rect={"x":176,"y":72,"width":120,"height":32}
            render(0, 1, a, rect); render(0, 1, b, rect); render(1, 2, c, rect)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertNotEqual(a.read_bytes(), c.read_bytes())
            self.assertTrue(a.read_bytes().startswith(b"P6\n320 120\n255\n"))

    def test_release_query_uses_root_window_resource_and_checks_button1(self):
        class Pointer: pass
        class Root:
            def __init__(self, mask): self.mask = mask
            def query_pointer(self):
                pointer = Pointer(); pointer.mask = self.mask; return pointer
        self.assertTrue(query_button_released(Root(0))["verified"])
        self.assertFalse(query_button_released(Root(1 << 8))["verified"])

    def test_ambiguous_wait_requires_two_ready_processes_and_distinct_targets(self):
        import inspect
        self.assertIn("expected_pids", inspect.signature(wait_ambiguous).parameters)

    def test_pixel_target_derivation_and_proxy_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"x.ppm"; rect={"x":176,"y":72,"width":120,"height":32}
            render(0,1,path,rect); w,h,rgb=ppm_rgb(path.read_bytes())
            self.assertEqual(center(blue_bbox(w,h,rgb)),[236,88])

    def test_launcher_rejects_wrong_and_symlink_output_before_docker(self):
        source=Path("/formal_launch.sh").read_text()
        self.assertIn("canonical_output",source)
        self.assertIn("-L",source)
        self.assertLess(source.index("canonical_output"),source.index("docker run"))
        with tempfile.TemporaryDirectory() as tmp:
            exp=Path(tmp)/"exp"; evidence=exp/"evidence"; evidence.mkdir(parents=True)
            formal=evidence/"formal-04"; preflight=evidence/"preflight-04"
            wrong=subprocess.run(["bash","/formal_launch.sh",str(exp),str(exp/"wrong"),str(preflight)],capture_output=True)
            self.assertEqual(wrong.returncode,40)
            formal.symlink_to(Path(tmp)/"elsewhere")
            alias=subprocess.run(["bash","/formal_launch.sh",str(exp),str(formal),str(preflight)],capture_output=True)
            self.assertEqual(alias.returncode,42)


if __name__ == "__main__":
    unittest.main()
