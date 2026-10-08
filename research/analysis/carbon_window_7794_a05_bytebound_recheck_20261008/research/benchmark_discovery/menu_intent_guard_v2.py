"""Strict proposal type gate around frozen local menu matcher."""
from menu_intent_guard_v1 import check as previous

def check(intent,*args):
 if type(intent) is not dict or set(intent)!={'intent','execute_once'} or type(intent['intent']) is not str or intent['execute_once'] is not True:
  return {'eligible':False,'reason':'invalid_intent_schema'}
 try:return previous(intent,*args)
 except (KeyError,TypeError,ValueError,IndexError,OverflowError):return {'eligible':False,'reason':'invalid_observation_metadata'}
