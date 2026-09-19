import unittest
from bridge import encode_request, validate_response

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.req = {"request_id": "r1"}
    def test_compatible_response_is_non_authoritative(self):
        result = validate_response(self.req, {"request_id":"r1", "status":"ok", "authority_granted":False, "payload":{"x":1}, "usage":{"input_tokens":1}})
        self.assertEqual(result.status, "COMPATIBLE"); self.assertFalse(result.authority_granted)
    def test_malformed_and_mismatch_refuse(self):
        self.assertEqual(validate_response(self.req, {"request_id":"r2"}).reason, "request_id_mismatch")
        self.assertEqual(validate_response(self.req, {"request_id":"r1", "status":"ok", "authority_granted":True}).reason, "authority_must_remain_false")
    def test_broker_error_yields(self):
        self.assertEqual(validate_response(self.req, {"request_id":"r1", "status":"error", "authority_granted":False, "error":"timeout"}).status, "YIELD")
    def test_request_encoding_requires_schema_hash(self):
        self.assertIn('"authority_granted": false', encode_request("r1", "a"*64, "probe"))
        with self.assertRaises(ValueError): encode_request("r1", "bad", "probe")

if __name__ == "__main__": unittest.main()
