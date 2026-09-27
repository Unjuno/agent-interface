"""Excluded construction: synthetic rows and child lifecycle, no timing block."""
import copy
import itertools
import os
import unittest
from pathlib import Path
import audit
import run


def synthetic():
    rows=[]
    for triplet,order in enumerate(list(itertools.permutations(run.ARMS))*5):
        for position,arm in enumerate(order):
            i=len(rows); wall0=1_000_000_000*(i+1); due0=wall0+9_000_000
            late={'IDLE':100_000,'SAME_CORE':3_000_000,'OTHER_CORE':110_000}[arm]
            samples=[[due0+j*2_000_000,due0+j*2_000_000+late,late] for j in range(300)]
            wall1=samples[-1][1]+100_000
            def identity(cpu,pid):
                return dict(pid=pid,tid=pid,cpu=cpu,affinity=[cpu],scheduler=0,nice=0)
            child=None
            if arm!='IDLE':
                cpu=0 if arm=='SAME_CORE' else 1
                child=dict(pid=100+i,observed_affinity=[cpu],returncode=0,stderr='',reaped=True,
                    ready=dict(kind='ready',identity=identity(cpu,100+i),monotonic_ns=wall0-100_000,process_ns=100),
                    terminal=dict(kind='stopped',identity=identity(cpu,100+i),monotonic_ns=wall1+100_000,process_ns=100_000,timed_out=False))
            rows.append(dict(triplet=triplet,position=position,arm=arm,before=identity(0,99),after=identity(0,99),
                     wall=[wall0,wall1],process=[100,1000],thread=[100,1000],samples=samples,stats=run.stats(samples),
                     child=child,child_alive_before=child is not None,child_alive_after=child is not None))
    return rows


def mutations(rows):
    changes={
      'missing_block':lambda r:r.pop(),
      'duplicate_block':lambda r:r.__setitem__(1,copy.deepcopy(r[0])),
      'missing_sample':lambda r:r[0]['samples'].pop(),
      'due_step':lambda r:r[0]['samples'][1].__setitem__(0,r[0]['samples'][1][0]+1),
      'wake_delta':lambda r:r[0]['samples'][1].__setitem__(1,r[0]['samples'][1][1]+1),
      'stored_late':lambda r:r[0]['samples'][1].__setitem__(2,r[0]['samples'][1][2]+1),
      'arm_identity':lambda r:r[0].__setitem__('arm','OTHER_CORE'),
      'observer_affinity':lambda r:r[0]['before'].__setitem__('affinity',[1]),
      'child_affinity':lambda r:r[2]['child'].__setitem__('observed_affinity',[0]),
      'summary_max':lambda r:r[0]['stats'].__setitem__('max_ns',r[0]['stats']['max_ns']+1),
      'missing_exit':lambda r:r[1]['child'].pop('returncode'),
      'bool_count':lambda r:r[0]['stats'].__setitem__('n',True),
      'bool_timestamp':lambda r:r[0]['samples'][0].__setitem__(2,False),
      'lost_load':lambda r:r[1]['child']['terminal'].__setitem__('process_ns',r[1]['child']['ready']['process_ns']),
    }
    results={}
    for name,change in changes.items():
        case=copy.deepcopy(rows); change(case)
        results[name]=bool(audit.reconstruct(case)['errors'])
    return results


class Study(unittest.TestCase):
    def test_synthetic_positive(self):
        result=audit.reconstruct(synthetic())
        self.assertEqual(result['errors'],[])
        self.assertEqual(result['decision'],'PASS_SAME_CORE_ATTRIBUTION_SCOPED')
        self.assertEqual(result['sample_count'],27000)
    def test_mutations(self):
        self.assertTrue(all(mutations(synthetic()).values()))
    def test_candidate_independent_agreement(self):
        rows=synthetic(); candidate=run.candidate_summary(rows); independent=audit.reconstruct(rows)
        for key in candidate: self.assertEqual(candidate[key],independent[key])
    def test_balanced_schedule(self):
        self.assertEqual(len(run.ORDERS),30)
        for position in range(3):
            for arm in run.ARMS:
                self.assertEqual(sum(order[position]==arm for order in run.ORDERS),10)
    def test_child_lifecycle_only(self):
        original=sorted(os.sched_getaffinity(0))
        for cpu in (0,1):
            p,ready,observed=run.start_child(cpu)
            result=run.finish_child(p,ready,observed)
            self.assertEqual(result['returncode'],0)
            self.assertTrue(result['reaped'])
            self.assertEqual(result['terminal']['identity']['affinity'],[cpu])
            self.assertFalse(result['terminal']['timed_out'])
        self.assertEqual(sorted(os.sched_getaffinity(0)),original)

if __name__=='__main__': unittest.main(verbosity=2)
