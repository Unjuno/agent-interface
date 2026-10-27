import unittest
from research.live_control.calc_compiled_stage_terminal_v1 import make_stage_executor

class StageExecutorTests(unittest.TestCase):
 def test_projection_is_delivered_before_return_and_detached(self):
  receipt={'format':'decision-receipt-v4','reported_state':'terminal','program_write_may_have_been_attempted':True,
    'terminals':[{'record':{'event':'terminal','status':'needs_decision','steps_completed':0,
    'release':{'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[]}}}]}
  calls=[]
  def run(payload): calls.append(('run',payload));return receipt
  def sink(value): calls.append(('sink',value));value['projection']['delivery']='mutated'; value['receipt'].clear()
  execute=make_stage_executor(run,sink)
  terminal=execute({'action':'inert'})
  self.assertEqual([v[0] for v in calls],['run','sink'])
  self.assertEqual(terminal['status'],'delivery_uncertain')
  self.assertEqual(receipt['terminals'][0]['record']['status'],'needs_decision')
 def test_sink_failure_is_propagated_without_retry(self):
  calls=[]
  def run(_):calls.append('run');return {}
  def sink(_):calls.append('sink');raise OSError('sink unavailable')
  with self.assertRaises(OSError):make_stage_executor(run,sink)({})
  self.assertEqual(calls,['run','sink'])