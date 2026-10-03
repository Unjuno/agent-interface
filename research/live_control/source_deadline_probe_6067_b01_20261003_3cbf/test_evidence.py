import copy
import json
import unittest
from evidence import check_trace, admit_launch

def snapshot(begin, usage):
    raw = 'usage_usec '+str(usage)+'\nnr_periods 0\nnr_throttled 0\nthrottled_usec 0\n'
    return {'begin_ns':begin,'end_ns':begin+3,'cpu_read_begin_ns':begin+1,'cpu_read_end_ns':begin+2,
            'cpu_stat_raw':raw,'cpu_stat':{'usage_usec':usage,'nr_periods':0,'nr_throttled':0,'throttled_usec':0},
            'process_cpu_ns':usage,'thread_cpu_ns':usage,'voluntary':usage,'involuntary':usage}

def trace():
    return {'due_ns':1000,'pre':snapshot(1,1),'wait':{'begin_ns':100,'return_ns':1000,
            'spin_enter_ns':100,'sleeps':[]},'post':snapshot(1001,2)}

class Evidence(unittest.TestCase):
    def test_coarse_overshoot_is_measured_and_missing_sleep_rejected(self):
        t={'due_ns':120_000_000,'pre':snapshot(99_999_996,1),
           'wait':{'begin_ns':100_000_000,'return_ns':121_000_000,'spin_enter_ns':None,
                   'sleeps':[{'start_ns':100_000_000,'return_ns':121_000_000,'requested_ns':5_000_000}]},
           'post':snapshot(121_000_001,2)}
        self.assertEqual(check_trace(t,121_000_005,121_000_006),
                         {'wait_lateness_ns':1_000_000,'post_wait_to_native_ns':5,'nr_throttled_delta':0,
                          'coarse_past_due':True,'sleep_overshoot_ns':[16_000_000]})
        t['wait']['sleeps']=[]
        with self.assertRaises(ValueError): check_trace(t,121_000_005,121_000_006)
    def test_complete_launch_admission_and_image_mutation(self):
        freeze={'producer_command':['frozen-launch'],'native_argv':['python3','-B','/src/probe.py','--out','/out/result'],
                'image_id':'sha256:fixture','guest_source':'/inputs/source','guest_output':'/outputs/raw',
                'effective_runtime':{'Entrypoint':None,'Runtime':'runc','Privileged':False,'CapAdd':None,'Tmpfs':{'/tmp':'rw,nosuid,size=64m'}}}
        state={'State':{'Status':'exited','ExitCode':0,'Running':False,'Paused':False,'Restarting':False,'OOMKilled':False,'Dead':False},
               'RestartCount':0,'Image':'sha256:fixture','Config':{'User':'501:501','Cmd':['python3','-B','/src/probe.py','--out','/out/result']},
               'HostConfig':{'Runtime':'runc','Privileged':False,'CapAdd':None,'Tmpfs':{'/tmp':'rw,nosuid,size=64m'},'NanoCpus':1000000000,'Memory':536870912,'MemorySwap':536870912,'PidsLimit':64,
                             'NetworkMode':'none','ReadonlyRootfs':True,'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges']},
               'Mounts':[{'Source':'/inputs/source','Destination':'/src','RW':False},{'Source':'/outputs/raw','Destination':'/out','RW':True}]}
        receipt={'exit_code':0,'inspect_exit':0,'command':['frozen-launch'],'inspect_stdout':json.dumps(state)}
        state['Config']['Entrypoint']=None
        receipt['inspect_stdout']=json.dumps(state)
        self.assertEqual(admit_launch(receipt,freeze)['State']['ExitCode'],0)
        for section,key,value in [('Config','Entrypoint',['sh']),('HostConfig','Runtime','other'),
                                  ('HostConfig','Privileged',True),('HostConfig','CapAdd',['SYS_ADMIN']),('HostConfig','Tmpfs',{})]:
            changed=copy.deepcopy(state); changed[section][key]=value
            changed_receipt={**receipt,'inspect_stdout':json.dumps(changed)}
            with self.subTest(key=key), self.assertRaises(ValueError): admit_launch(changed_receipt,freeze)
        for key,value in [('Running',True),('Status','running')]:
            changed=copy.deepcopy(state); changed['State'][key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):
                admit_launch({**receipt,'inspect_stdout':json.dumps(changed)},freeze)
        state['Image']='sha256:other'
        receipt['inspect_stdout']=json.dumps(state)
        with self.assertRaises(ValueError): admit_launch(receipt,freeze)
    def test_clock_and_counter_delta_are_reconstructed(self):
        self.assertEqual(check_trace(trace(),1005,1006),
                         {'wait_lateness_ns':0,'post_wait_to_native_ns':5,'nr_throttled_delta':0,'coarse_past_due':False,'sleep_overshoot_ns':[]})
    def test_impossible_early_and_unbound_spin_are_rejected(self):
        for due,spin in [(100_000_000,100),(1000,101)]:
            t=trace(); t['due_ns']=due; t['wait']['return_ns']=due; t['wait']['spin_enter_ns']=spin
            t['post']=snapshot(due+1,2)
            with self.subTest(due=due), self.assertRaises(ValueError): check_trace(t,due+5,due+6)
    def test_no_spin_return_is_exact_final_sample(self):
        t=trace(); t['wait'].update(begin_ns=1000,return_ns=1001,spin_enter_ns=None)
        t['post']=snapshot(1002,2)
        with self.assertRaises(ValueError): check_trace(t,1006,1007)
        t={'due_ns':120_000_000,'pre':snapshot(99_999_996,1),
           'wait':{'begin_ns':100_000_000,'return_ns':122_000_000,'spin_enter_ns':None,
                   'sleeps':[{'start_ns':100_000_000,'return_ns':121_000_000,'requested_ns':5_000_000}]},
           'post':snapshot(122_000_001,2)}
        with self.assertRaises(ValueError): check_trace(t,122_000_005,122_000_006)
    def test_post_snapshot_must_finish_before_native_call(self):
        with self.assertRaises(ValueError): check_trace(trace(),1002,1006)
    def test_false_cpu_count_is_not_zero(self):
        t=trace(); t['post']['cpu_stat']['nr_throttled']=False
        with self.assertRaises(ValueError): check_trace(t,1005,1006)
    def test_required_counter_raw_join_is_not_optional(self):
        t=trace(); t['post']['cpu_stat_raw']='usage_usec 99\nnr_periods 0\nnr_throttled 0\nthrottled_usec 0\n'
        with self.assertRaises(ValueError): check_trace(t,1005,1006)
    def test_missing_wait_mechanism_is_invalid(self):
        t=trace(); t['wait']['spin_enter_ns']=None
        with self.assertRaises(ValueError): check_trace(t,1005,1006)
    def test_nonzero_native_exit_is_never_admitted(self):
        with self.assertRaises(ValueError): admit_launch({'exit_code':2},{})
    def test_incomplete_launch_custody_is_never_admitted(self):
        with self.assertRaises(ValueError):
            admit_launch({'exit_code':0,'inspect_exit':0,'inspect_stdout':json.dumps({'State':{'Running':True}})}, {})

if __name__=='__main__': unittest.main()
