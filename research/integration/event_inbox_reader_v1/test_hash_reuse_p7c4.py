"""Regression for #4432: reuse hash state only inside one read_pending call."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from research.integration.event_inbox_reader_v1 import reader

class HashReuseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/"events.jsonl"
        self.lines=[(json.dumps({"event":"observation","delivery_id":f"delivery:{i}","text":f"row-{i}"})+"\n").encode() for i in range(1,4)]
        self.data=b"".join(self.lines); self.path.write_bytes(self.data)
    def cursor(self,n,stream="unit"):
        prefix=b"".join(self.lines[:n])
        return {"schema":reader.SCHEMA,"stream_id":stream,"offset":len(prefix),
                "prefix_sha256":hashlib.sha256(prefix).hexdigest(),"next_sequence":n+1}
    def traced(self,cur,page=1):
        constructors=[]; updates=[]
        class H:
            def __init__(self,data=b""): constructors.append(bytes(data)); self.h=hashlib.sha256(data)
            def update(self,data): updates.append(bytes(data)); self.h.update(data)
            def hexdigest(self): return self.h.hexdigest()
        with patch.object(reader,"hashlib",SimpleNamespace(sha256=H)):
            result=reader.read_pending(self.path,stream_id="unit",cursor=cur,max_records=page)
        return result,constructors,updates
    def test_verified_prefix_reused_once(self):
        cur=self.cursor(1); before=json.dumps(cur,sort_keys=True)
        result,constructors,updates=self.traced(cur)
        self.assertEqual(constructors,[self.lines[0]]); self.assertEqual(updates,[self.lines[1]])
        self.assertEqual(result["next_cursor"],self.cursor(2)); self.assertEqual(json.dumps(cur,sort_keys=True),before)
        self.assertEqual(self.path.read_bytes(),self.data)
    def test_each_call_freshly_rehashes_current_prefix(self):
        for n in (1,2,1):
            result,constructors,_=self.traced(self.cursor(n))
            self.assertEqual(constructors,[b"".join(self.lines[:n])]); self.assertEqual(result["next_cursor"],self.cursor(n+1))
    def test_changed_prefix_still_refuses(self):
        cur=self.cursor(1); self.path.write_bytes(self.data.replace(b"row-1",b"ROW-1",1))
        with self.assertRaisesRegex(ValueError,"CURSOR_PREFIX_CHANGED"):
            reader.read_pending(self.path,stream_id="unit",cursor=cur)
    def test_blocked_line_not_in_returned_cursor(self):
        self.path.write_bytes(self.lines[0]+self.lines[1]+b"bad\n")
        result,constructors,updates=self.traced(self.cursor(1),32)
        self.assertEqual(result["tail_state"],"blocked"); self.assertEqual(result["next_cursor"],self.cursor(2))
        self.assertEqual(constructors,[self.lines[0]]); self.assertEqual(updates,[self.lines[1]])
    def test_incomplete_tail_does_not_advance(self):
        self.path.write_bytes(self.lines[0]+self.lines[1][:-1])
        result,_,updates=self.traced(self.cursor(1))
        self.assertEqual(result["tail_state"],"incomplete"); self.assertEqual(result["next_cursor"],self.cursor(1)); self.assertEqual(updates,[b""])
    def test_empty_and_terminal_exact(self):
        result,_,updates=self.traced(self.cursor(3)); self.assertEqual(result["records"],[]); self.assertEqual(result["next_cursor"],self.cursor(3)); self.assertEqual(updates,[b""])
        self.path.write_bytes(b""); result,constructors,updates=self.traced(None)
        self.assertEqual(constructors,[b""]); self.assertEqual(updates,[b""]); self.assertEqual(result["next_cursor"],self.cursor(0))
    def test_interleaved_streams_do_not_share_digest_state(self):
        left=reader.read_pending(self.path,stream_id="left",max_records=1)
        other=self.path.with_name("other.jsonl"); other.write_bytes(self.data.replace(b"row-",b"alt-"))
        right=reader.read_pending(other,stream_id="right",max_records=1)
        last=reader.read_pending(self.path,stream_id="left",cursor=left["next_cursor"],max_records=1)
        self.assertEqual(last["next_cursor"],self.cursor(2,"left"))
        self.assertNotEqual(left["next_cursor"]["prefix_sha256"],right["next_cursor"]["prefix_sha256"])
if __name__=="__main__": unittest.main()
