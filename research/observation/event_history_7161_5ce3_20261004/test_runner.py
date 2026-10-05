import subprocess,sys,unittest
from pathlib import Path
from run_stage import call
class Runner(unittest.TestCase):
    def test_timeout_preserves_command_and_partial_output(self):
        args=[sys.executable,'-B','-c','import time; print("partial",flush=True); time.sleep(1)']
        try:r=call(args,timeout=0.2)
        except Exception as e:self.fail('timeout evidence lost: '+type(e).__name__)
        self.assertEqual(r['command'],args);self.assertIsNone(r['exit'])
        self.assertEqual(r['error'],'TimeoutExpired');self.assertIn('partial',r['stdout'])
    def test_missing_executable_retains_os_error(self):
        try:r=call(['/nonexistent-event-history-7161-executable'])
        except Exception as e:self.fail('command evidence lost: '+type(e).__name__)
        self.assertIsNone(r['exit']);self.assertEqual(r['error'],'FileNotFoundError')
    def test_optimized_runner_refuses_admission(self):
        p=subprocess.run([sys.executable,'-B','-O','-c','import run_stage'],cwd=Path(__file__).parent,capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertIn('STOP_OPTIMIZED_RUNNER_UNSUPPORTED',p.stderr)
if __name__=='__main__':unittest.main()
