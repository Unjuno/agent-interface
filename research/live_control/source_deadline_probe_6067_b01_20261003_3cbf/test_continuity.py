import copy
import unittest
from evidence import check_continuity, check_shared_cpu, admit_transport
from test_evidence import snapshot, trace

def receipt(command, start, end):
    return {'command':command,'started_ns':start,'finished_ns':end,'exit_code':0,'stdout':'','stderr':''}

def custody():
    frozen={k:[k] for k in ('hash_command','idle_command','mkdir_command','inspect_command','copy_command')}
    before=receipt(['hash_command'],1,2)
    idle=receipt(['idle_command'],3,4)
    consumed={'mode':'source-boundary-diagnostic','started_ns':5,
              'readiness':{'guest_sha256':before,'idle':idle},'mkdir':receipt(['mkdir_command'],6,7)}
    launch={'started_ns':8,'finished_ns':9,'inspection':receipt(['inspect_command'],10,11),
            'inspect_exit':0,'inspect_stdout':'','inspect_stderr':''}
    copied=receipt(['copy_command'],12,13)
    after=receipt(['hash_command'],14,15)
    return consumed,launch,copied,after,frozen

class Continuity(unittest.TestCase):
    def test_complete_transport_and_one_host_clock(self):
        self.assertIsNone(admit_transport(*custody()))
    def test_wrong_transport_command_status_mode_and_order(self):
        original=custody()
        mutations=[(0,('mode',),'formal'),(0,('readiness','idle','command'),['wrong']),
                   (0,('readiness','guest_sha256','exit_code'),2),(0,('readiness','idle','stdout'),'busy'),
                   (0,('mkdir','command'),['wrong']),(1,('inspection','command'),['wrong']),
                   (2,('command',),['wrong']),(3,('command',),['wrong']),
                   (2,('started_ns',),9),(3,('started_ns',),12),(1,('inspect_stdout',),'different')]
        for index,path,value in mutations:
            args=copy.deepcopy(original); obj=args[index]
            for key in path[:-1]: obj=obj[key]
            obj[path[-1]]=value
            with self.subTest(path=path,index=index), self.assertRaises(ValueError): admit_transport(*args)
    def test_stream_process_counters_and_native_chronology(self):
        previous=trace(); current=trace()
        current['pre']=snapshot(1010,3)
        self.assertIsNone(check_continuity(previous,current,1006))
        current['pre']=snapshot(1010,1)
        with self.assertRaises(ValueError): check_continuity(previous,current,1006)
        current['pre']=snapshot(1005,3)
        with self.assertRaises(ValueError): check_continuity(previous,current,1006)
    def test_shared_cgroup_disjoint_reads_only(self):
        self.assertIsNone(check_shared_cpu([snapshot(10,3),snapshot(1,2)]))
        with self.assertRaises(ValueError): check_shared_cpu([snapshot(1,3),snapshot(10,2)])
        # Overlapping brackets have no established read order.
        self.assertIsNone(check_shared_cpu([snapshot(1,3),snapshot(1,2)]))

if __name__=='__main__': unittest.main()
