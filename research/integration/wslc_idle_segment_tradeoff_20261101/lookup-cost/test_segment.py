import random
import unittest
from segment import SegmentedAppendMap


class SegmentTests(unittest.TestCase):
    def test_forks_remain_isolated_when_both_append(self):
        original=SegmentedAppendMap(4)
        for n in range(1,20):original.append(n,{'seq':n})
        left=original.fork();right=original.fork()
        left.append(21,{'seq':21});right.append(22,{'seq':22});original.append(20,{'seq':20})
        self.assertEqual(list(original),list(range(1,21)))
        self.assertEqual(list(left),list(range(1,20))+[21])
        self.assertEqual(list(right),list(range(1,20))+[22])
        for history, missing in ((original,21),(left,20),(right,20)):
            with self.assertRaises(KeyError):history[missing]
        for n in range(1,20):
            self.assertIs(original[n],left[n]);self.assertIs(left[n],right[n])

    def test_sparse_keys_match_dict_and_shallow_value_semantics(self):
        rng=random.Random(2142);keys=sorted(rng.sample(range(1,20000),1000))
        segment=SegmentedAppendMap(16);baseline={}
        for key in keys:
            value={'seq':key};segment.append(key,value);baseline[key]=value
        self.assertEqual(list(segment),list(baseline));self.assertEqual(len(segment),len(baseline))
        for key in keys:self.assertIs(segment[key],baseline[key])
        for key in (0,20001):
            with self.assertRaises(KeyError):segment[key]

    def test_rejects_non_monotonic_and_invalid_keys(self):
        segment=SegmentedAppendMap(2);segment.append(2,'a')
        for key in (0,1,2,True,1.5,'3'):
            with self.subTest(key=key),self.assertRaises(ValueError):segment.append(key,'b')
        self.assertEqual(list(segment),[2])

    def test_partial_and_full_chunk_boundaries(self):
        for size in (1,2,4,7):
            segment=SegmentedAppendMap(size)
            for n in range(1,31):
                old=segment.fork();segment.append(n,n)
                self.assertEqual(len(old),n-1)
                with self.assertRaises(KeyError):old[n]
                self.assertEqual(segment[n],n)

if __name__=='__main__':unittest.main()
