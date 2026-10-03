"""Complete literal cell fixtures; authoritative joins and temporal attribution."""
import base64
import copy
import hashlib
import struct
import unittest
from test_validation import example
from validation import validate_cell,snapshot_valid

def full_snapshot(s,cpu=1000):
    s.update(process_cpu_ns=cpu,thread_cpu_ns=cpu,voluntary=0,involuntary=0,
             cpu_stat_local={'available':True,'raw':'throttled_usec 0\n','error':None},
             schedstat={'available':True,'raw':'1 0 1\n','error':None},
             schedstats_enabled={'available':True,'raw':'0\n','error':None})
    return s
def fixture():
    epoch=1_000_000_000; events=[]; waits=[]; journal=[]; frames=[]; obs=[]
    for i in range(8):
        e,d,c=example(); shift=epoch-88_000_000+120_000_000*i
        e['id']=d['id']=c['id']=i+1; e['color']=0xFF0000 if (i+1)%2 else 0x00FF00
        for k in ('onset_ns','due_clear_ns','draw_start_ns','draw_end_ns','clear_start_ns','clear_end_ns'): e[k]+=shift
        for w in (d,c):
            for k in ('due_ns','paint_start_ns','paint_end_ns'): w[k]+=shift
            for k in ('begin_ns','return_ns','spin_enter_ns'): w['wait'][k]+=shift
            for s in (w['pre'],w['post']):
                for k in ('begin_ns','end_ns','cpu_read_begin_ns','cpu_read_end_ns'): s[k]+=shift
                full_snapshot(s,1000+10000*i)
        d['pre']['process_cpu_ns']=d['pre']['thread_cpu_ns']=900+10000*i
        d['post']['process_cpu_ns']=1002+10000*i; d['post']['thread_cpu_ns']=1001+10000*i
        for s in (c['pre'],c['post']): s['process_cpu_ns']=s['thread_cpu_ns']=1010+10000*i
        for k in ('begin_ns','end_ns'): d['trial'][k]+=shift
        for k in ('process_cpu_before_ns','process_cpu_after_ns','thread_cpu_before_ns','thread_cpu_after_ns'): d['trial'][k]+=10000*i
        events.append(e); waits.extend([d,c])
        journal.extend([{'event':k,'id':i+1,'start':e[k+'_start_ns'],'end':e[k+'_end_ns']} for k in ('draw','clear')])
        due=epoch+(120*i+10*[0,3,6,9][i%4]+5)*1_000_000
        pre=copy.deepcopy(d['pre']); post=copy.deepcopy(d['post'])
        for k in ('begin_ns','end_ns','cpu_read_begin_ns','cpu_read_end_ns'):
            pre[k]=due-2_000_000; post[k]=due+1000
        full_snapshot(pre,1000+10000*i); full_snapshot(post,1001+10000*i)
        trace={'index':i,'due_ns':due,'pre':pre,'post':post,
               'wait':{'begin_ns':due-1_000_000,'return_ns':due,'spin_enter_ns':due-1_000_000,'sleeps':[]}}
        pixels=bytes(4096)
        frames.append({**copy.deepcopy(trace),'start_ns':due+2000,'native_return_ns':due+3000,
                       'extracted_ns':due+4000,'pixels_b64':base64.b64encode(pixels).decode(),
                       'pixel_sha256':hashlib.sha256(pixels).hexdigest(),'decoded':None})
        obs.append(trace)
    source={'pid':101,'window':7,'epoch_ns':epoch,'treatment':'full','events':events,'wait_traces':waits,
            'final_pixels':[0]*1024,'final_keymap':'00'*32}
    capture={'pid':102,'window':7,'epoch_ns':epoch,'epoch_read_ns':epoch-50_000_000,
             'initial_keymap':'00'*32,'final_keymap':'00'*32,'frames':frames}
    life={'fixture_pid':101,'observer_pid':102,'xvfb_pid':103,
          'fixture_exit':0,'observer_exit':0,'xvfb_exit':0,
          'xvfb_running_before_cleanup':True,'xvfb_shutdown_requested':'SIGTERM'}
    data={'source':source,'capture':capture,'lifecycle':life,'source_journal':journal,
          'source_waits':copy.deepcopy(waits),'frames':copy.deepcopy(frames),'observer_waits':obs,
          'epoch':{'epoch_ns':epoch},'fixture_ready':{'pid':101,'window':7},
          'observer_ready':{'pid':102,'initial_keymap':'00'*32},
          'display_ready':{'pid':103,'display':':0','transport':'child-owned-displayfd'}}
    spec={'id':'p0_full','kind':'pulse','pair':0,'treatment':'full','phase':1,'width_ms':10,'offsets':[0,3,6,9]}
    return spec,data

class CellTests(unittest.TestCase):
    def test_complete_cell_preserves_bad_exposure_outcome(self):
        result=validate_cell(*fixture())
        self.assertEqual(len(result['events']),8)
        self.assertFalse(result['scientific_exposure_eligible'])

    def test_authoritative_epoch_mismatch(self):
        spec,data=fixture(); data['epoch']['epoch_ns']+=1
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_readiness_window_mismatch(self):
        spec,data=fixture(); data['fixture_ready']['window']+=1
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_boolean_pid(self):
        spec,data=fixture(); data['lifecycle']['fixture_pid']=data['source']['pid']=True
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_private_display_owner_mismatch(self):
        spec,data=fixture(); data['display_ready']['pid']=104
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_future_cue_pixels_temporally_impossible(self):
        spec,data=fixture(); raw=struct.pack('<1024I',1,*([0xFF0000]*1023))
        for frame in (data['capture']['frames'][0],data['frames'][0]):
            frame['pixels_b64']=base64.b64encode(raw).decode(); frame['pixel_sha256']=hashlib.sha256(raw).hexdigest()
            frame['decoded']={'id':1,'color':0xFF0000}
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_planned_sigterm_keeps_native_children_zero(self):
        spec,data=fixture(); data['lifecycle']['xvfb_exit']=-15
        try: result=validate_cell(spec,data)
        except ValueError as exc: self.fail('planned shutdown rejected: '+str(exc))
        self.assertEqual(len(result['events']),8)

    def test_unexpected_server_zero_exit_not_planned_shutdown(self):
        spec,data=fixture(); data['lifecycle']['xvfb_running_before_cleanup']=False
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_killed_server_is_not_normal_shutdown(self):
        spec,data=fixture(); data['lifecycle']['xvfb_exit']=-9
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_cpu_regression_even_with_matching_raw(self):
        spec,data=fixture()
        for w in (data['source']['wait_traces'][0],data['source_waits'][0]):
            w['post']['cpu_stat']['usage_usec']=0
            w['post']['cpu_stat_raw']=w['post']['cpu_stat_raw'].replace('usage_usec 1','usage_usec 0')
        with self.assertRaises(ValueError): validate_cell(spec,data)

    def test_optional_thread_cpu_corruption(self):
        s=full_snapshot(copy.deepcopy(example()[1]['pre'])); s['thread_cpu_ns']=-1
        with self.assertRaises(ValueError): snapshot_valid(s)

if __name__=='__main__': unittest.main()
