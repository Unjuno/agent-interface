"""Passive diagnostic must be finite and never create input authority."""
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from map01_post_cross_diagnostic import collect

class DiagnosticTests(unittest.TestCase):
    def test_three_neutral_frames_are_timestamped_and_lossless(self):
        with tempfile.TemporaryDirectory() as directory:
            ticks=iter([10,20,30,40,50,60])
            waits=[]
            result=collect(Path(directory), capture=lambda: Image.new("RGB",(2,2),(1,2,3)),
                           neutral=lambda: True, clock=lambda: next(ticks), wait=waits.append)
            self.assertEqual(waits,[0.0,0.1,0.1])
            self.assertEqual(len(result["frames"]),3)
            self.assertEqual([x["capture_ns"] for x in result["frames"]],[20,40,60])
            self.assertTrue(all(x["neutral"] is True for x in result["frames"]))
            self.assertEqual([x["file"] for x in result["frames"]],
                             ["post-cross-0.png","post-cross-1.png","post-cross-2.png"])
            for row in result["frames"]:
                with Image.open(Path(directory)/row["file"]) as im:
                    self.assertEqual(im.getpixel((0,0)),(1,2,3))
            self.assertEqual(result["authority"],"none")

    def test_non_neutral_state_aborts_before_saving(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,"neutral"):
                collect(Path(directory), capture=lambda: self.fail("must not capture"),
                        neutral=lambda: False, clock=lambda: 1, wait=lambda _: None)
            self.assertEqual(list(Path(directory).iterdir()),[])

if __name__=="__main__":
    unittest.main()
