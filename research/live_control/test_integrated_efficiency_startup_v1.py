"""Finite POSIX endpoint-pipe and failed-start cleanup regressions; no GUI."""
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import integrated_efficiency_client_v1 as m
from integrated_efficiency_client_v1 import read_endpoint

class EndpointTests(unittest.TestCase):
 def invoke(self,data,*,keep_open=False,max_bytes=65536):
  rd,wr=os.pipe();stream=os.fdopen(rd,'rb');result=[]
  def reader():
   try:result.append(('ok',read_endpoint(stream,timeout=.04,max_bytes=max_bytes)))
   except Exception as e:result.append(('error',type(e).__name__))
  # Classification data is ready before the reader's short deadline starts.
  # Silent/partial-line deadline cases keep their original timeout unchanged.
  if data:os.write(wr,data)
  if not keep_open:os.close(wr);wr=None
  t=threading.Thread(target=reader);t.start()
  try:
   t.join(.3);finished=not t.is_alive()
  finally:
   if wr is not None:os.close(wr)
   t.join(1);stream.close()
  self.assertFalse(t.is_alive(),'reader remains after pipe closure')
  return finished,result
 def test_silent_endpoint_has_internal_deadline(self):
  finished,result=self.invoke(b'',keep_open=True);self.assertTrue(finished,'silent reader exceeded deadline');self.assertEqual(result,[('error','TimeoutError')])
 def test_partial_line_has_internal_deadline(self):
  finished,result=self.invoke(b'{"socket":',keep_open=True);self.assertTrue(finished,'partial reader exceeded deadline');self.assertEqual(result,[('error','TimeoutError')])
 def test_empty_eof_is_classified(self):self.assertEqual(self.invoke(b'')[1],[('error','EOFError')])
 def test_fragmented_endpoint(self):
  rd,wr=os.pipe();stream=os.fdopen(rd,'rb')
  def write():
   try:
    for fragment in [b'{"socket":',b'"/owned/',b'socket"}\n']:
     os.write(wr,fragment);time.sleep(.005)
   finally:os.close(wr)
  t=threading.Thread(target=write);t.start()
  try:self.assertEqual(read_endpoint(stream,timeout=.2),{'socket':'/owned/socket'})
  finally:t.join(1);stream.close()
  self.assertFalse(t.is_alive())
 def test_valid_endpoint(self):self.assertEqual(self.invoke(b'{"socket":"/owned/socket"}\n')[1],[('ok',{'socket':'/owned/socket'})])
 def test_oversize(self):self.assertEqual(self.invoke(b'x'*100+b'\n',max_bytes=32)[1],[('error','ValueError')])
 def test_missing_socket(self):self.assertEqual(self.invoke(b'{}\n')[1],[('error','ValueError')])
 def test_malformed_json(self):self.assertEqual(self.invoke(b'{oops}\n')[1],[('error','JSONDecodeError')])

class BadClose:
 def close(self):raise OSError('stdout close lost')
class ExitedProcess:
 stdout=BadClose()
 def poll(self):return 0
class CleanupTests(unittest.TestCase):
 def test_cleanup_close_cannot_replace_primary_or_skip_remaining_resources(self):
  with tempfile.TemporaryDirectory() as root:
   client=m.RuntimeClient(Path(root)/'case',1)
   try:
    with patch.object(m.subprocess,'Popen',return_value=ExitedProcess()),patch.object(m,'read_endpoint',side_effect=TimeoutError('primary endpoint timeout')):
     with self.assertRaisesRegex(TimeoutError,'primary endpoint timeout') as caught:client.start(endpoint_timeout=.01)
    self.assertTrue(client.errors.closed)
    self.assertFalse(Path(client.temporary.name).exists())
    self.assertTrue(any('stdout close lost' in note for note in caught.exception.__notes__))
   finally:
    if client.errors is not None:client.errors.close()
    if client.temporary is not None:client.temporary.cleanup()


import subprocess
import sys
import pathlib
class StartupFailures(unittest.TestCase):
 def exercise(self,stage):
  original=subprocess.Popen
  def launch(args,**kw):return original([sys.executable,'-u','-c','import time; print(\'{"socket":"/unused/q04.sock"}\',flush=True); time.sleep(20)'],**kw)
  reply={'reply':{'records':[{'event':'ready'}]},'continuation':{}}
  with tempfile.TemporaryDirectory(prefix='q04-regression-') as root:
   c=m.RuntimeClient(pathlib.Path(root)/'client',1)
   target={'request':'request_once','ready':'first','journal':'initialize'}[stage]
   try:
    with patch.object(m.subprocess,'Popen',side_effect=launch),patch.object(m,'request_once',return_value=reply),patch.object(m,target,side_effect=RuntimeError('primary-'+stage)):
     with self.assertRaisesRegex(RuntimeError,'primary-'+stage):c.start(endpoint_timeout=1)
    self.assertIsNotNone(c.process.poll(),'owned child survives failed startup')
    self.assertTrue(c.process.stdout.closed)
    self.assertTrue(c.errors.closed)
    self.assertFalse(pathlib.Path(c.temporary.name).exists())
   finally:c.close()
 def test_request_failure(self):self.exercise('request')
 def test_ready_failure(self):self.exercise('ready')
 def test_journal_failure(self):self.exercise('journal')

if __name__=='__main__':unittest.main(verbosity=2)
