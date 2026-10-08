import copy
import json
import unittest
from model_contract import parse
from audit import model_value

def events():
    return [{'type':'thread.started','thread_id':'unit-five-fields'},
        {'type':'item.completed','item':{'type':'agent_message','text':'{"decision":"INSERT_PREFIX","observed_target":"dv","observed_decoy":"","prefix":"h"}'}},
        {'type':'turn.completed','usage':{'input_tokens':91,'cached_input_tokens':4,'cache_write_input_tokens':0,'output_tokens':17,'reasoning_output_tokens':8}}]

class UsageTests(unittest.TestCase):
    def test_five_fields_preserved_separately_by_both_parsers(self):
        want={'input_tokens':91,'cached_input_tokens':4,'cache_write_input_tokens':0,'output_tokens':17,'reasoning_output_tokens':8}
        for parser in (parse,model_value):
            with self.subTest(parser=parser.__name__):
                try:result=parser(events())
                except ValueError as exc:self.fail('known five-field usage unsupported: '+str(exc))
                self.assertEqual(result['usage'],want)

    def test_unknown_boolean_negative_missing_or_excess_cached_refused(self):
        changes=[lambda u:u.update(unknown=1),lambda u:u.update(cache_write_input_tokens=True),
            lambda u:u.update(reasoning_output_tokens=-1),lambda u:u.pop('output_tokens'),
            lambda u:u.update(cached_input_tokens=92)]
        for parser in (parse,model_value):
            for change in changes:
                rows=events();change(rows[-1]['usage'])
                with self.subTest(parser=parser.__name__,usage=rows[-1]['usage']):
                    with self.assertRaises(ValueError):parser(rows)

if __name__=='__main__':unittest.main()
