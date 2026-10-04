import importlib.util
import struct
import unittest
import zlib

class AuditTests(unittest.TestCase):
    def test_independent_pixel_audit_rejects_coherent_png_change(self):
        self.assertIsNotNone(importlib.util.find_spec('audit'),'independent pixel audit missing')
        from audit import pixel_errors
        from xwd_png import convert
        header=[104,7,2,24,2,1,0,0,32,0,32,32,8,4,0xff0000,0xff00,0xff,8,256,0,2,1,0,0,0]
        raw=struct.pack('>25I',*header)+b'tst\0'+bytes([0,0,255,0,0,255,0,0])
        self.assertEqual(pixel_errors(raw,convert(raw)),[])
        changed=raw[:-4]+bytes([255,0,0,0])
        self.assertIn('pixel_identity',pixel_errors(raw,convert(changed)))

    def test_model_stream_is_recomputed_not_candidate_answer(self):
        self.assertIsNotNone(importlib.util.find_spec('audit'),'independent event audit missing')
        from audit import model_value
        rows=[{'type':'thread.started','thread_id':'independent'},
            {'type':'item.completed','item':{'type':'agent_message','text':'{"decision":"REFUSE","observed_target":"","observed_decoy":"hsn","prefix":""}'}},
            {'type':'turn.completed','usage':{'input_tokens':30,'cached_input_tokens':0,'output_tokens':9}}]
        self.assertEqual(model_value(rows)['answer']['decision'],'REFUSE')
        with self.assertRaises(ValueError):model_value(rows+rows[1:2])
        with self.assertRaises(ValueError):model_value(rows+[{'type':'item.started','item':{'type':'command_execution'}}])

if __name__=='__main__':unittest.main()
