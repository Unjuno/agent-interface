import copy
import hashlib
import json
import unittest
import os
import time
import subprocess
import sys
from pipe_audit import pipe_errors


def packet():
    value={'schema':'issue5260-a09-focus-pipe-v1','token':'fresh','pid':17,
        'target_id':42,'freeze_sha256':'a'*64,'kind':'FocusIn','widget':'target',
        'focus_get':'target','sequence':1,'event_ns':100,'written_ns':101}
    blob=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    digest=hashlib.sha256(blob).hexdigest()
    return {'token':'fresh','app_pid':17,'ready':{'geometry':{'target_id':42}},
        'app':{'events':[{'kind':'FocusIn','widget':'target','sequence':1,'monotonic_ns':100}],
            'focus_pipe':{'identity':{'fd':5,'inode':80,'nonblocking':True,'pipe_buf':4096},
                'first_error':None,'close':{'fd':5,'started_ns':130,'completed_ns':131},
                'publications':[{'value':value,'trace':{'frame_utf8':blob.decode(),
                    'sha256':digest,'requested_bytes':len(blob),'written_bytes':len(blob),
                    'write_error':None,'started_ns':102,'completed_ns':110}}]}},
        'pipe':{'identity':{'read_fd':4,'write_fd':5,'read_inode':80,'write_inode':80,'pipe_buf':4096},
            'reads':[{'status':'DATA','started_ns':103,'completed_ns':105,'hex':blob.hex(),
                'bytes':len(blob),'sha256':digest},
                {'status':'EOF','started_ns':132,'completed_ns':133,'hex':'','bytes':0,
                 'sha256':hashlib.sha256(b'').hexdigest()}],
            'frames':[{'value':copy.deepcopy(value),'seen_ns':105}],'eof':True,
            'closes':[{'name':'write_fd','fd':5,'started_ns':90,'completed_ns':91},
                      {'name':'read_fd','fd':4,'started_ns':134,'completed_ns':135}]}}


class AuditTests(unittest.TestCase):
    @unittest.skipUnless(os.name=='posix','Linux pipe identity audit')
    def test_actual_producer_transport_records_pass_independent_audit(self):
        from pipe_transport import PipeSession
        with PipeSession() as session:
            child=subprocess.Popen([sys.executable,'-c',
                "import json,os,sys,time; from focus_pipe import FocusPipe; "
                "p=FocusPipe(int(sys.argv[1]),{'token':'fresh','pid':os.getpid(),'target_id':42,'freeze_sha256':'a'*64}); "
                "e={'kind':'FocusIn','widget':'target','sequence':1,'monotonic_ns':time.monotonic_ns()}; "
                "p.publish(e,'target'); p.close(); print(json.dumps({'events':[e],'focus_pipe':p.snapshot()}))",
                str(session.write_fd)],pass_fds=(session.write_fd,),stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,text=True)
            session.release_parent_writer()
            stdout,stderr=child.communicate(timeout=3)
            self.assertEqual(child.returncode,0)
            self.assertEqual(stderr,'')
            session.drain();session.close()
            row={'token':'fresh','app_pid':child.pid,'ready':{'geometry':{'target_id':42}},
                'app':json.loads(stdout),
                'pipe':{'identity':session.identity,'reads':session.reads,'frames':session.frames,
                    'eof':session.eof,'closes':session.closes}}
            self.assertEqual(pipe_errors(row,'a'*64),[])

    def test_literal_packet_allows_receive_before_write_returns(self):
        self.assertEqual(pipe_errors(packet(),'a'*64),[])

    def test_mutated_bytes_identity_event_and_close_are_rejected(self):
        mutations=[
            lambda r:r['pipe']['reads'][0].update(hex='00'),
            lambda r:r['pipe']['frames'][0].update(seen_ns=106),
            lambda r:r['app']['focus_pipe']['publications'][0]['value'].update(pid=18),
            lambda r:r['app']['events'][0].update(monotonic_ns=99),
            lambda r:r['pipe']['identity'].update(pipe_buf=511),
            lambda r:r['pipe']['identity'].update(write_inode=81),
            lambda r:r['app']['focus_pipe']['identity'].update(nonblocking=False),
            lambda r:r['pipe'].update(eof=False),
            lambda r:r['pipe']['closes'].pop(),
            lambda r:r['app']['focus_pipe'].update(first_error={'failure':True}),
            lambda r:r['app']['focus_pipe']['publications'][0]['trace'].update(written_bytes=1),
            lambda r:r['pipe']['frames'][0]['value'].update(sequence=True),
            lambda r:r['app']['focus_pipe']['publications'][0]['trace'].update(started_ns=True),
        ]
        for mutate in mutations:
            row=packet();mutate(row)
            with self.subTest(mutation=mutations.index(mutate)):
                self.assertTrue(pipe_errors(row,'a'*64))


if __name__=='__main__':unittest.main()
