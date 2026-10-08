import unittest
from audit import decode

class AuditTests(unittest.TestCase):
    def test_wire_decoder_rejects_bad_magic(self):
        with self.assertRaises(ValueError):
            decode(b'NOPE'+b'\0'*4, None, 'x', 1)

if __name__ == '__main__':
    unittest.main()
