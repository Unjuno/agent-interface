Warning: truncated output (original token count: 841)
Total output lines: 46

"""Construction-only corruption tests for independent row auditor."""
import base64,hashlib,io,json,pathlib,subprocess,sys,tempfile,torch
ROOT=pathlib.Path(__file__).resolve().parent
def data(n,seed,f…741 tokens truncated…rejected(self):
   x=fixture();x["measurements"]["snapshots"]["B"]["sha256"]="0"*64
   r=run(x);self.assertFalse(r["integrity"]);self.assertIn("B:learned_sha",r["errors"])
 unittest.main(verbosity=2)
