"""Small distinct construction controls, not the frozen30-row comparison."""
import asyncio
import copy
import json
import unittest
from candidate import observe_case
from audit import encoded


class ConstructionTests(unittest.IsolatedAsyncioTestCase):
    def payload(self):
        return {'generation':3,'target':'construction','answer':{'visible':False,'coordinates':[42,17]},
                'evidence_role':'construction-only'}

    async def test_standard_shallow_copy_still_shares_nested_answer(self):
        row=await observe_case('shallow_delivery','caller_nested',self.payload())
        self.assertTrue(row['identity']['same_answer']);self.assertTrue(row['b_final']['answer']['visible'])
        self.assertEqual(row['read_calls'],1);self.assertTrue(row['waiter_tasks_terminal'])

    async def test_deep_delivery_cannot_freeze_owner_before_reuse(self):
        row=await observe_case('deep_delivery','owner_nested',self.payload())
        self.assertFalse(row['identity']['same_answer']);self.assertTrue(row['b_final']['answer']['visible'])

    async def test_completion_bytes_preserve_original_owner_value(self):
        value=self.payload();row=await observe_case('json_completion','owner_nested',value)
        self.assertEqual(encoded(row['b_final']),encoded(value))
        self.assertFalse(row['identity']['same_answer']);self.assertEqual(row['read_calls'],1)

    def test_oracle_identity_retains_json_boolean_integer_float_distinctions(self):
        self.assertNotEqual(encoded(True),encoded(1));self.assertNotEqual(encoded(1),encoded(1.0))
        value={'a':[True,1,1.0]};self.assertEqual(json.loads(encoded(value)),value)


if __name__=='__main__':unittest.main()
