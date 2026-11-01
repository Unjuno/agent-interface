"""Dictionary-visible semantics for an experimental segmented history index."""
import unittest
import random
from runtime.guarded_x11_v1.hybrid_records import HybridRecords


class HybridRecordsTests(unittest.TestCase):
    def test_fork_isolation_append_overwrite_delete_and_clear(self):
        parent=HybridRecords();parent[1]='one';parent[2]='two';child=parent.copy()
        child[3]='three';parent[2]='changed';parent[4]='four'
        self.assertEqual(list(parent),[1,2,4]);self.assertEqual(list(child),[1,2,3])
        self.assertEqual(parent[2],'changed');self.assertEqual(child[2],'two')
        del parent[1];child.clear()
        self.assertEqual(list(parent),[2,4]);self.assertEqual(list(child),[])
        with self.assertRaises(KeyError):child[1]

    def test_dict_equivalent_numeric_keys_and_fallback_order(self):
        actual=HybridRecords();expected={}
        for key,value in [(1,'one'),(2,'two'),(True,'bool-overwrite'),('x','text'),(1.0,'float-overwrite'),(-1,'negative')]:
            actual[key]=value;expected[key]=value
        self.assertEqual(list(actual),list(expected))
        for key in [1,True,1.0,2,'x',-1]:self.assertEqual(actual[key],expected[key])
        with self.assertRaises(TypeError):actual[[]]
        copy=actual.copy();del actual[2]
        self.assertEqual(copy[2],'two');self.assertNotIn(2,actual)

    def test_fast_path_handles_equal_bool_and_float_queries(self):
        actual=HybridRecords();actual[1]='one';actual[2]='two'
        self.assertEqual(actual[True],'one');self.assertEqual(actual[1.0],'one')
        with self.assertRaises(KeyError):actual[3.0]
        self.assertEqual(list(actual),[1,2])

    def test_clear_resets_segment_and_does_not_change_fork(self):
        records=HybridRecords()
        for n in range(1,514):records[n]=n
        fork=records.copy();records.clear();records[1]='new'
        self.assertEqual(len(fork),513);self.assertEqual(fork[513],513)
        self.assertEqual(list(records),[1]);self.assertEqual(records[1],'new')

    def test_seeded_mapping_operations_match_dict_across_forks(self):
        rng=random.Random(589);pairs=[(HybridRecords(),{})]
        keys=[-2,0,1,2,3,4,5,True,1.0,'x','y']
        for _ in range(600):
            actual,expected=rng.choice(pairs);key=rng.choice(keys);op=rng.randrange(5)
            if op==0 and len(pairs)<8:
                pairs.append((actual.copy(),expected.copy()))
            elif op==1:
                actual.clear();expected.clear()
            elif op==2:
                if key in expected:del actual[key];del expected[key]
                else:
                    with self.assertRaises(KeyError):del actual[key]
            else:
                value=rng.randrange(100000);actual[key]=value;expected[key]=value
            for history,reference in pairs:
                self.assertEqual(list(history),list(reference))
                self.assertEqual(len(history),len(reference))
                for present,value in reference.items():self.assertEqual(history[present],value)

    def test_iterator_rejects_size_change_like_dict(self):
        records=HybridRecords();records[1]='one';records[2]='two'
        iterator=iter(records);self.assertEqual(next(iterator),1);records[3]='three'
        with self.assertRaises(RuntimeError):next(iterator)

    def test_iterator_allows_value_overwrite_like_dict(self):
        records=HybridRecords();records[1]='one';records[2]='two'
        iterator=iter(records);self.assertEqual(next(iterator),1);records[2]='changed'
        self.assertEqual(list(iterator),[2]);self.assertEqual(records[2],'changed')

if __name__=='__main__':unittest.main()
