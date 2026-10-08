import importlib.util
import json
import struct
import unittest
import zlib

class ContractTests(unittest.TestCase):
    def test_xwd_literal_pixels_and_bad_layout(self):
        self.assertIsNotNone(importlib.util.find_spec('xwd_png'),'XWD converter missing')
        from xwd_png import convert
        header=[104,7,2,24,2,1,0,0,32,0,32,32,8,4,0xff0000,0xff00,0xff,8,256,0,2,1,0,0,0]
        raw=struct.pack('>25I',*header)+b'tst\0'+bytes([0,0,255,0,0,255,0,0])
        png=convert(raw)
        self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
        offset=8; chunks=[]
        while offset<len(png):
            length=struct.unpack('>I',png[offset:offset+4])[0]
            name=png[offset+4:offset+8]; data=png[offset+8:offset+8+length]
            self.assertEqual(struct.unpack('>I',png[offset+8+length:offset+12+length])[0],zlib.crc32(name+data)&0xffffffff)
            chunks.append((name,data)); offset+=12+length
        self.assertEqual(zlib.decompress(next(v for k,v in chunks if k==b'IDAT')),b'\0\xff\0\0\0\xff\0')
        for bad in (raw[:-1],bytes(104),struct.pack('>25I',*header[:11],24,*header[12:])+raw[100:]):
            with self.assertRaises(ValueError):convert(bad)

    def test_completed_answer_and_real_usage(self):
        self.assertIsNotNone(importlib.util.find_spec('model_contract'),'model parser missing')
        from model_contract import parse
        answer={'decision':'INSERT_PREFIX','observed_target':'vr','observed_decoy':'','prefix':'h'}
        rows=[{'type':'thread.started','thread_id':'fixture-thread'},
            {'type':'item.completed','item':{'type':'agent_message','text':json.dumps(answer)}},
            {'type':'turn.completed','usage':{'input_tokens':20,'cached_input_tokens':0,'output_tokens':12}}]
        self.assertEqual(parse(rows),{'answer':answer,'usage':rows[-1]['usage'],'call_id':'fixture-thread'})
        for changed in (rows[:-1],rows+rows[-1:],rows+[{'type':'item.completed','item':{'type':'command_execution'}}],
                rows[:-1]+[{'type':'turn.completed','usage':{'input_tokens':True,'cached_input_tokens':0,'output_tokens':12}}]):
            with self.assertRaises(ValueError):parse(changed)

    def test_visual_oracle_does_not_treat_decoy_or_ambiguous_as_prefix(self):
        self.assertIsNotNone(importlib.util.find_spec('review_audit'),'independent oracle missing')
        from review_audit import expected
        self.assertEqual(expected('hqu','hqu',''),{'decision':'NO_REPAIR','observed_target':'hqu','observed_decoy':'','prefix':''})
        self.assertEqual(expected('hvr','vr',''),{'decision':'INSERT_PREFIX','observed_target':'vr','observed_decoy':'','prefix':'h'})
        self.assertEqual(expected('hsn','','hsn')['decision'],'REFUSE')
        self.assertEqual(expected('htm','xm','')['decision'],'REFUSE')

if __name__=='__main__':unittest.main()
