"""Read-only reconstruction of the retained G10 OCR image inputs and outputs.

No OCR process, live GUI, native input or original experiment code is run.
"""
import hashlib, io, json, unittest
from pathlib import Path, PurePosixPath
from PIL import Image, ImageOps

ROOT=Path(__file__).parent/'calc_current_shared_3311_4d74_20261004'/'calc-compiled-ocrlive-4d74'/'runs'/'compiled_ocrlive10'
BOXES=((37,161,124,175),(127,161,215,175),(217,161,305,175))

class RetainedG10OCRInputs(unittest.TestCase):
 def test_saved_frame_crop_and_ocr_attempt_associations(self):
  raw_bytes=(ROOT/'raw.json').read_bytes();log_bytes=(ROOT/'OCR_ATTEMPTS.jsonl').read_bytes()
  self.assertEqual(hashlib.sha256(raw_bytes).hexdigest(),'890c68f13e5fa8598bcbb2f456b8ee5319c584249c19492744a7c96f170014bf')
  self.assertEqual(hashlib.sha256(log_bytes).hexdigest(),'2494317855edb657ba1875fe1262925a5e30df6dd8f8617230f6fcfe90f7ce59')
  raw=json.loads(raw_bytes);attempts=[json.loads(x) for x in log_bytes.splitlines()]
  self.assertEqual((len(raw['images']),len(raw['pixel_checks']),len(attempts)),(3,3,7))
  groups=[]
  for frame,check in zip(raw['images'],raw['pixel_checks']):
   artifact=frame['native']['artifact'];name=PurePosixPath(artifact['path']).name
   self.assertEqual(artifact['path'],'/out/guarded/images/'+name)
   data=(ROOT/'guarded'/'images'/name).read_bytes()
   self.assertEqual(hashlib.sha256(data).hexdigest(),artifact['sha256'])
   group=[a for a in attempts if a['source']==artifact['path']];groups.append(len(group))
   with Image.open(io.BytesIO(data)) as im:
    image=im.convert('RGB')
    self.assertEqual(hashlib.sha256(image.crop(tuple(check['region'])).tobytes()).hexdigest(),check['rgb_sha256'])
    outputs=[]
    for index,a in enumerate(group):
     self.assertLess(index,len(BOXES));crop_name=PurePosixPath(a['crop']).name
     self.assertEqual(a['crop'],'/out/'+crop_name);self.assertTrue(crop_name.startswith('ocr-'))
     box=BOXES[index];expected=ImageOps.expand(image.crop(box).resize((4*(box[2]-box[0]),4*(box[3]-box[1]))),border=20,fill='white')
     with Image.open(ROOT/crop_name) as saved:self.assertEqual(saved.convert('RGB').tobytes(),expected.tobytes())
     self.assertEqual(a['exit_code'],0);self.assertGreaterEqual(a['start_ns'],frame['native']['capture_ended_ns'])
     self.assertGreaterEqual(a['end_ns'],a['start_ns']);outputs.append(a['stdout'].strip())
   self.assertEqual(outputs,[''] if check['decoded_values'] is None else check['decoded_values'])
  self.assertEqual(groups,[1,3,3]);self.assertEqual(sum(groups),len(attempts))