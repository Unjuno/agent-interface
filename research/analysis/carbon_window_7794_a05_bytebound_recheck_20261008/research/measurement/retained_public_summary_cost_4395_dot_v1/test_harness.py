import copy
import itertools
import json
import unittest

import oracle
import harness
import run_once


class Construction(unittest.TestCase):
    def test_exact_external_json_spacing_and_order(self):
        # Changing to canonical separators/sort_keys must fail this test.
        self.assertEqual(harness.wire_bytes({'z': 1, 'a': 'é'}), b'{"z": 1, "a": "\\u00e9"}')

    def test_external_image_is_removed_not_serialized(self):
        self.assertEqual(harness.wire_bytes({'image': {'opaque': 1}, 'v': 2}), b'{"v": 2}')

    def test_all_six_orders_are_balanced(self):
        self.assertEqual(harness.orders(), list(itertools.permutations(('FULL_V3', 'PACED_BRIEF', 'PUBLIC_SUMMARY'))))

    def test_typed_equality_does_not_conflate_bool_and_int(self):
        self.assertFalse(oracle.same({'flag': True}, {'flag': 1}))

    def test_timing_gate_accepts_finite_aggregate(self):
        self.assertEqual(oracle.timing_errors({'wall_ns': 100000, 'cpu_ns': 99000, 'count': 3}, 1000), [])

    def test_timing_gate_rejects_coarse_or_nonfinite(self):
        rows=[{'wall_ns': 999, 'cpu_ns': 900, 'count': 3}, {'wall_ns': float('nan'), 'cpu_ns': 9, 'count': 3}, {'wall_ns': True, 'cpu_ns': 9, 'count': 3}]
        self.assertTrue(all(oracle.timing_errors(r, 1000) for r in rows))

    def test_full_oracle_is_exact_and_not_aliased(self):
        source={'authority':'none','outcome_summary':{'execution_status':'refused'},'receipt':{'x':[1]}}
        expected=oracle.expected_view('refusal', 'FULL_V3', source, None)
        self.assertEqual(expected, source)
        self.assertIsNot(expected, source)

    def test_real_refusal_policy_contract_cannot_be_success(self):
        source={'authority':'none','outcome_summary':{'execution_status':'refused'},'receipt':{'x':[1]}}
        for policy in ('PACED_BRIEF','PUBLIC_SUMMARY'):
            self.assertEqual(oracle.expected_view('refusal',policy,source,None), source)

    def test_expected_summary_preserves_critical_fields(self):
        source={'authority':'none','call_id':'construct-0','session':{'state':'open'},'outcome_summary':{'execution_status':'completed'},'image_reference':{'sha256':'x'},'receipt':{'source':{'sha256':'x','bytes':1},'source_extra':None}}
        expected=copy.deepcopy(source)
        self.assertEqual(oracle.preserved_errors(source, expected), [])
        expected['outcome_summary']['execution_status']='refused'
        self.assertTrue(oracle.preserved_errors(source, expected))

    def test_memory_counts_are_typed_and_ordered(self):
        self.assertEqual(oracle.memory_errors({'net_bytes':30,'peak_bytes':50}), [])
        self.assertTrue(oracle.memory_errors({'net_bytes':True,'peak_bytes':50}))
        self.assertTrue(oracle.memory_errors({'net_bytes':51,'peak_bytes':50}))

    def test_fixed_batch_retains_all_outputs_and_exact_call_count(self):
        calls=[]
        def producer(v):
            calls.append(v)
            return v
        row, outputs=harness.batch(producer, {'x':1}, 3, measured=False)
        self.assertEqual(len(calls),3)
        self.assertEqual(outputs,[b'{"x": 1}']*3)
        self.assertEqual(row,{'count':3})

    def test_timed_batch_has_integer_nonnegative_brackets(self):
        row, outputs=harness.batch(lambda x:x, {'construction':True}, 3, measured=True)
        self.assertEqual(len(outputs),3)
        self.assertTrue(all(type(row[k]) is int and row[k]>=0 for k in ('wall_ns','cpu_ns')))

    def test_zero_empty_clock_median_is_not_semantic_failure(self):
        clock={'empty_brackets':[[10,0] for _ in range(64)],'wall_resolution_ns':1,'cpu_resolution_ns':1,'empty_wall_median_low_ns':10,'empty_cpu_median_low_ns':0,'minimum_ns':1000}
        self.assertEqual(oracle.clock_errors(clock),[])
        self.assertEqual(run_once.outcome_for(['timing:0:cpu_ns:granularity_or_type']),'STOP_CLOCK_GRANULARITY')

    def test_final_receipt_can_retain_partial_failed_output(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'root';out=Path(directory)/'out';root.mkdir();out.mkdir()
            (root/'code').write_bytes(b'fixed');(out/'STOP.json').write_text('{"status":"STOP"}')
            before={'code':run_once.sha(b'fixed')}
            receipt=run_once.final_receipt(root,out,before,'a'*64,None)
            self.assertEqual(receipt['source_after'],before)
            self.assertIn('STOP.json',receipt['output_hashes'])
            self.assertIn('observed_rlimit_as',receipt)


if __name__ == '__main__':
    unittest.main()
