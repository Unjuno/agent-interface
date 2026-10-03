import sys,pathlib,importlib.util,tempfile,unittest
from unittest.mock import patch
import integrated_efficiency_client_v1 as m
class StagingTests(unittest.TestCase):
 def check_interrupt(self,kind):
  with tempfile.TemporaryDirectory() as outer:
   c=m.RuntimeClient(pathlib.Path(outer),1);c.temporary=tempfile.TemporaryDirectory();c.journal=pathlib.Path(c.temporary.name)/'journal.jsonl';c.journal.write_bytes(b'original journal evidence');diag=pathlib.Path(str(c.journal)+'.invalid-response.json');diag.write_bytes(b'original diagnostic evidence');primary=ValueError('original validation error')
   def interrupt(incoming,outgoing):outgoing.write(incoming.read(4));outgoing.flush();raise kind('copy interrupted')
   try:
    with patch.object(m.shutil,'copyfileobj',interrupt):c.__exit__(ValueError,primary,None)
    self.assertTrue(c.journal.exists());self.assertFalse(c.temporary._finalizer.alive)
    self.assertFalse((c.root/'journal.jsonl').exists())
    self.assertEqual(list(c.root.iterdir()),[])
    c.close()
    self.assertEqual((c.root/'journal.jsonl').read_bytes(),b'original journal evidence');self.assertEqual((c.root/diag.name).read_bytes(),b'original diagnostic evidence');self.assertFalse(pathlib.Path(c.temporary.name).exists())
   finally:c.temporary.cleanup()
 def test_keyboard_interrupt_can_resume_custody(self):self.check_interrupt(KeyboardInterrupt)
 def test_system_exit_can_resume_custody(self):self.check_interrupt(SystemExit)
class RaceTests(unittest.TestCase):
 def setUp(self):
  self.outer=tempfile.TemporaryDirectory();self.c=m.RuntimeClient(pathlib.Path(self.outer.name),1);self.c.temporary=tempfile.TemporaryDirectory();self.c.journal=pathlib.Path(self.c.temporary.name)/'journal.jsonl';self.c.journal.write_bytes(b'original journal evidence');self.diag=pathlib.Path(str(self.c.journal)+'.invalid-response.json');self.diag.write_bytes(b'original diagnostic evidence');self.real_link=m.os.link
 def tearDown(self):self.c.temporary.cleanup();self.outer.cleanup()
 def preserved(self):
  self.assertTrue(self.c.journal.exists());self.assertEqual(self.c.journal.read_bytes(),b'original journal evidence');self.assertEqual(self.diag.read_bytes(),b'original diagnostic evidence');self.assertFalse(self.c.temporary._finalizer.alive);self.assertFalse(any(p.name.startswith('.custody-') for p in self.c.root.iterdir()))
 def test_identical_destination_race_is_accepted(self):
  def race(source,dest):dest.write_bytes(source.read_bytes());self.real_link(source,dest)
  with patch.object(m.os,'link',race):self.c.close()
  self.assertFalse(pathlib.Path(self.c.temporary.name).exists());self.assertEqual((self.c.root/self.diag.name).read_bytes(),b'original diagnostic evidence')
 def test_conflicting_destination_race_preserves_original(self):
  def race(source,dest):dest.write_bytes(b'other evidence');self.real_link(source,dest)
  with patch.object(m.os,'link',race):
   with self.assertRaises(FileExistsError):self.c.close()
  self.preserved();self.assertEqual((self.c.root/'journal.jsonl').read_bytes(),b'other evidence')
 def test_unsupported_link_preserves_original(self):
  with patch.object(m.os,'link',side_effect=OSError('unsupported hard link')):
   with self.assertRaises(OSError):self.c.close()
  self.preserved();self.assertEqual(list(self.c.root.iterdir()),[])
 def test_staging_readback_corruption_is_not_published(self):
  def corrupt(incoming,outgoing):outgoing.write(b'corrupt copy')
  with patch.object(m.shutil,'copyfileobj',corrupt):
   with self.assertRaises(OSError):self.c.close()
  self.preserved();self.assertEqual(list(self.c.root.iterdir()),[])
 def test_interrupt_after_link_can_resume_complete_destination(self):
  def interrupt(source,dest):self.real_link(source,dest);raise KeyboardInterrupt('after exclusive publication')
  with patch.object(m.os,'link',interrupt):
   with self.assertRaises(KeyboardInterrupt):self.c.close()
  self.preserved();self.assertEqual((self.c.root/'journal.jsonl').read_bytes(),b'original journal evidence');self.c.close();self.assertEqual((self.c.root/self.diag.name).read_bytes(),b'original diagnostic evidence')
if __name__=='__main__':unittest.main()

