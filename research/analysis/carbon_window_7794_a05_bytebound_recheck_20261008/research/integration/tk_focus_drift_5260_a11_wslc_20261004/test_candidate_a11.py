import os,time,unittest
import candidate
from pipe_transport import PipeSession
from pipe_receipt import encode_frame

class CandidateTests(unittest.TestCase):
    def test_six_fresh_idle_rows_in_three_arms(self):
        rows=candidate.planned_rows({'seed':52611026,'replicates_per_cell':2})
        self.assertEqual(len(rows),6)
        self.assertEqual(sorted(r['mode'] for r in rows),
            ['DRIFT_REFUSE']*2+['DRIFT_STALE_CONTROL']*2+['STABLE']*2)
        self.assertEqual({r['load'] for r in rows},{'idle'})
        self.assertEqual(len({(r['mode'],r['replicate']) for r in rows}),6)
    def test_all_treatments_validate_both_fields_before_xlib(self):
        geometry={w+'_'+f:20 for w in ('target','decoy','save')
                  for f in ('root_x','root_y','width','height')}
        for mode in ('STABLE','DRIFT_REFUSE','DRIFT_STALE_CONTROL'):
            try:
                selected=candidate.click_geometry({'geometry':geometry},
                    dict(mode=mode,instrumentation_mode='MEMORY_ONLY'))
            except RuntimeError as e:
                self.fail('valid A11 treatment not implemented: '+str(e))
            self.assertEqual(selected,'target')
        geometry['decoy_width']=True
        with self.assertRaisesRegex(RuntimeError,'STOP_CLICK_GEOMETRY'):
            candidate.click_geometry({'geometry':geometry},
                dict(mode='DRIFT_REFUSE',instrumentation_mode='MEMORY_ONLY'))
    def phase(self,mode,initial='ADMITTED'):
        self.assertTrue(hasattr(candidate,'post_admission'),'post-admission integration missing')
        binding=dict(token='new',pid=17,target_id=42,freeze_sha256='a'*64)
        read,write=os.pipe()
        os.set_blocking(read,False)
        try:
            with PipeSession() as s:
                def intervene():
                    start=time.monotonic_ns()
                    for kind,seq,widget in [('FocusOut',2,'target'),('FocusIn',3,'decoy')]:
                        value=dict(binding,schema='issue5260-a09-focus-pipe-v1',
                            kind=kind,sequence=seq,widget=widget,focus_get='other',
                            event_ns=time.monotonic_ns(),written_ns=time.monotonic_ns())
                        os.write(s.write_fd,encode_frame(value))
                    return dict(started_ns=start,completed_ns=time.monotonic_ns())
                result=candidate.post_admission({'status':initial,'ack':{'sequence':1}},
                    mode,s,binding,intervene,lambda ch:os.write(write,ch.encode()),
                    lambda:os.write(write,b'S'),{'payload':'hxy','drift_timeout_ms':10,
                    'ack_poll_ms':1,'ack_max_age_ms':50})
                os.close(write);write=None
                return result,os.read(read,100),len(s.reads)
        finally:
            os.close(read)
            if write is not None:os.close(write)
    def test_real_pipe_observed_drift_refuses_without_payload(self):
        r,data,reads=self.phase('DRIFT_REFUSE')
        self.assertEqual(r['dispatch']['status'],'REFUSED')
        self.assertEqual(r['drift']['status'],'OBSERVED_DRIFT')
        self.assertEqual(data,b'')
        self.assertGreater(reads,0)
    def test_explicit_stale_control_emits_once_after_real_pipe_drift(self):
        r,data,_=self.phase('DRIFT_STALE_CONTROL')
        self.assertEqual(r['dispatch']['status'],'EMITTED')
        self.assertEqual(data,b'hxyS')
    def test_initial_refusal_never_intervenes_or_emits(self):
        r,data,reads=self.phase('DRIFT_STALE_CONTROL','REFUSED')
        self.assertEqual(r['dispatch']['status'],'STOP')
        self.assertIsNone(r['intervention'])
        self.assertEqual(data,b'')
        self.assertEqual(reads,0)

if __name__=='__main__':unittest.main()
