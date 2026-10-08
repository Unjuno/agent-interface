import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tile_transport import Frame
from image_artifact import ImageArtifactSink


class ImageArtifactTest(unittest.TestCase):
    def test_exactness_reference_and_missing_file_recovery(self):
        for level in (1,6):
            with tempfile.TemporaryDirectory() as directory:
                sink=ImageArtifactSink(directory,compress_level=level)
                frame=Frame(11,9,"RGB",bytes(11*9*3))
                a=sink.publish(frame); b=sink.publish(frame)
                self.assertEqual(a['image'],b['image']); self.assertTrue(b['image_reused'])
                changed=Frame(11,9,"RGB",b'\x01'+frame.pixels[1:])
                c=sink.publish(changed)
                self.assertFalse(c['image_reused'])
                with Image.open(c['image']) as im: self.assertEqual(im.tobytes(),changed.pixels)
                Path(c['image']).unlink()
                d=sink.publish(changed)
                self.assertFalse(d['image_reused'])
                with Image.open(d['image']) as im: self.assertEqual(im.tobytes(),changed.pixels)


if __name__=='__main__': unittest.main()
