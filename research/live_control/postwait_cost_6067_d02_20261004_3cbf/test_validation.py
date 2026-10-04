"""Literal clock brackets catch treatment omission and erroneous censoring."""
import copy
import unittest
from validation import validate_event

def example():
    event = {'id':1,'color':0xFF0000,'onset_ns':100_000_000,'due_clear_ns':110_000_000,
             'draw_start_ns':107_000_000,'draw_end_ns':108_000_000,
             'clear_start_ns':111_000_000,'clear_end_ns':112_000_000}
    def snap(begin, end):
        return {'begin_ns':begin,'end_ns':end,'cpu_read_begin_ns':begin,
                'cpu_read_end_ns':end,'cpu_stat':{'usage_usec':1,'nr_periods':1,
                'nr_throttled':0,'throttled_usec':0},
                'cpu_stat_raw':'usage_usec 1\nnr_periods 1\nnr_throttled 0\nthrottled_usec 0\n',
                'process_cpu_ns':900 if begin==90_000_000 else 1002 if begin==102_000_000 else 1011,
                'thread_cpu_ns':900 if begin==90_000_000 else 1001 if begin==102_000_000 else 1011,
                'voluntary':0,'involuntary':0,
                **{name:{'available':False,'raw':None,'error':{'errno':2,'message':'literal absent'}}
                   for name in ('cpu_stat_local','schedstat','schedstats_enabled')}}
    draw = {'kind':'draw','id':1,'due_ns':100_000_000,'pre':snap(90_000_000,95_000_000),
            'wait':{'begin_ns':96_000_000,'return_ns':101_000_000,'spin_enter_ns':96_000_000,'sleeps':[]},
            'post':snap(102_000_000,105_000_000),'trial':{
                'begin_ns':101_000_000,'end_ns':106_000_000,
                'process_cpu_before_ns':1000,'process_cpu_after_ns':1003,
                'thread_cpu_before_ns':1000,'thread_cpu_after_ns':1002},
            'paint_start_ns':107_000_000,'paint_end_ns':108_000_000}
    clear = {'kind':'clear','id':1,'due_ns':110_000_000,'pre':snap(108_000_000,109_000_000),
             'wait':{'begin_ns':109_000_000,'return_ns':110_000_000,'spin_enter_ns':109_000_000,'sleeps':[]},
             'post':snap(110_000_000,111_000_000),'trial':None,
             'paint_start_ns':111_000_000,'paint_end_ns':112_000_000}
    return event,draw,clear

class ValidationTests(unittest.TestCase):
    def test_short_exposure_is_measured_not_censored(self):
        row=validate_event(*example(),'full')
        self.assertEqual(row['delay_ns'],6_000_000)
        self.assertEqual(row['exposure_ns'],3_000_000)
        self.assertEqual(row['trial_wall_ns'],5_000_000)
        self.assertEqual(row['trial_thread_cpu_ns'],2)

    def test_full_snapshot_must_not_be_omitted(self):
        args=list(example()); args[1]['post']=None
        with self.assertRaises(ValueError): validate_event(*args,'full')

    def test_minimal_must_not_silently_do_full_snapshot(self):
        with self.assertRaises(ValueError): validate_event(*example(),'minimal')

    def test_minimal_null_post_is_valid(self):
        args=list(example()); args[1]['post']=None
        self.assertEqual(validate_event(*args,'minimal')['snapshot_wall_ns'],0)

    def test_cpu_outside_wall_bracket_rejected(self):
        args=list(example()); args[1]['trial']['thread_cpu_after_ns']=10_000_000
        with self.assertRaises(ValueError): validate_event(*args,'full')

    def test_backwards_draw_join_rejected(self):
        args=list(example()); args[1]['wait']['return_ns']=108_000_000
        with self.assertRaises(ValueError): validate_event(*args,'full')

    def test_boolean_timestamp_rejected(self):
        args=list(example()); args[0]['draw_start_ns']=True
        with self.assertRaises(ValueError): validate_event(*args,'full')

if __name__=='__main__': unittest.main()
