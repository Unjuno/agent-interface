import unittest
from preflight import prepare, Rejected, fingerprint

MAP = [[ord('a'), ord('A')], [ord('-'), ord('_')], [ord('1'), ord('!')], [32,32], [0xFFE1,0]]

class Tests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(prepare('aA-_1! ', MAP).strokes, ((8,False),(8,True),(9,False),(9,True),(10,False),(10,True),(11,False)))
    def test_underscore_shift(self):
        self.assertEqual(prepare('_',MAP).strokes, ((9,True),))
    def test_whole_suffix(self):
        for text in ('aaa\n', 'aaa\t', 'aaa\0', 'aaa東京', 'aaa\ud800', 'aaa\x7f'):
            with self.assertRaises(Rejected): prepare(text,MAP)
    def test_missing_symbol(self):
        with self.assertRaises(Rejected): prepare('ab',MAP)
    def test_missing_shift(self):
        with self.assertRaises(Rejected): prepare('aA',MAP[:-1])
    def test_empty(self):
        self.assertEqual(prepare('',MAP).strokes, ())
    def test_limit(self):
        self.assertEqual(len(prepare('a'*16384,MAP).strokes),16384)
        with self.assertRaises(Rejected): prepare('a'*16385,MAP)
    def test_types(self):
        for x in (None, True, 3, [], b'a'):
            with self.assertRaises(Rejected): prepare(x,MAP)
    def test_malformed_map(self):
        for x in (None, 2, 'abc', (), [], [[1]], [[True,3]], [[-1,0]], [[1,'A']]):
            with self.assertRaises(Rejected): prepare('a',x)
    def test_first_code(self):
        for x in (False, 0, 256, 254):
            with self.assertRaises(Rejected): prepare('a',MAP,x)
    def test_level_preference(self):
        self.assertEqual(prepare('a', [[0,97],[97,65],[0xFFE1,0]]).strokes,((9,False),))
    def test_map_binding(self):
        p=prepare('a',MAP); changed=[r[:] for r in MAP]; changed[0][0]=98
        self.assertNotEqual(p.map_hash, fingerprint(changed))
    def test_exhaustive_ascii(self):
        for i in range(128):
            if chr(i) in 'aA-_1! ': self.assertEqual(len(prepare(chr(i),MAP).strokes),1)
            else:
                with self.assertRaises(Rejected): prepare(chr(i),MAP)

if __name__ == '__main__': unittest.main()
