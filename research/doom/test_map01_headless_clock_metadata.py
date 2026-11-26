import unittest,struct,zlib,io
from PIL import Image
from map01_candidate_setup_evidence_v1 import headless_clock_metadata_consistent, png_clock_words, EvidenceError

class HeadlessClockMetadataTests(unittest.TestCase):
 def test_rejects_hex_and_words_that_disagree(self):
  self.assertFalse(headless_clock_metadata_consistent(
   {'saved_ptic_words':[35,869],'saved_ptic_raw_hex':'00000023000002ca'}))
  self.assertTrue(headless_clock_metadata_consistent(
   {'saved_ptic_words':[35,869],'saved_ptic_raw_hex':'0000002300000365'}))
 def test_png_clock_is_unique_and_crc_checked(self):
  def chunk(kind,data):
   return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
  pt=chunk(b'ptIc',struct.pack('>II',35,869))
  end=chunk(b'IEND',b'')
  signature=b'\x89PNG\r\n\x1a\n'
  header=chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))
  buf=io.BytesIO();Image.new('RGB',(1,1)).save(buf,format='PNG')
  image=buf.getvalue();png=image[:-12]+pt+end
  self.assertEqual(png_clock_words(png),[35,869])
  for bad in (png[:-1],png+b'bad',image[:-12]+pt+pt+end,
              signature+header+pt+end,signature+header+header+pt+end,png[:12]+b'X'+png[13:]):
   with self.subTest(bad=bad),self.assertRaises(EvidenceError):png_clock_words(bad)
 def test_rejects_incomplete_or_bad_metadata(self):
  for row in ({'saved_ptic_words':[35,869]}, {'saved_ptic_raw_hex':'0000002300000365'},
              {'saved_ptic_words':[True,869],'saved_ptic_raw_hex':'0000000100000365'}):
   with self.subTest(row=row):self.assertFalse(headless_clock_metadata_consistent(row))
if __name__=='__main__':unittest.main()
