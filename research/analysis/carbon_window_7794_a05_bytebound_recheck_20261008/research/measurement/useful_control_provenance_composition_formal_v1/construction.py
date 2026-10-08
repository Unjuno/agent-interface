from __future__ import annotations
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
MEAS=HERE.parent
sys.path.insert(0,str(MEAS/'useful_control_interval_contract_v1'))
sys.path.insert(0,str(MEAS/'useful_control_provenance_composition_v1'))
sys.path.insert(0,str(HERE))
from interval_contract import Actuation, EffectEvent, Interval, ReleaseReceipt
from composed_contract import EffectRecord, analyze_composed
from oracle import oracle_analyze

W=Interval(0,20)
A=Actuation(5,ReleaseReceipt(10,12,False),[Interval(4,8)],' a ')
controls=[
    [EffectRecord('e1',EffectEvent(5,' a ',True,True))],
    [EffectRecord('e1',EffectEvent(15,' a ',True,True))],
    [EffectRecord('e1',EffectEvent(-1,' a ',False,True))],
    [EffectRecord('e1',EffectEvent(4,' a ',False,True))],
    [EffectRecord('e1',EffectEvent(7,'missing',True,True))],
    [EffectRecord('e1',EffectEvent(7,'missing',True,False))],
    [EffectRecord('e1',EffectEvent(-1,'   ',True,True))],
]
for records in controls:
    expected=oracle_analyze(W,[A],records)
    assert expected[0]=='ok'
    got=analyze_composed(W,[A],records)
    assert got==expected[1],(records,got,expected)
# Gate precedence plumbing only; no formal seeds.
for acts,records,msg in [
    ([Actuation(5,ReleaseReceipt(10,12,False),[], '   ')],[EffectRecord('',EffectEvent(-1,'',True,True))],'invalid actuation_id'),
    ([A,A],[EffectRecord('',EffectEvent(-1,'',True,True))],'duplicate actuation_id'),
    ([A],[EffectRecord('',EffectEvent(-1,'',True,True))],'invalid effect_id'),
    ([A],[EffectRecord('e',EffectEvent(6,' a ',True,True)),EffectRecord('e',EffectEvent(7,' a ',True,True))],'duplicate effect_id'),
]:
    expected=oracle_analyze(W,acts,records)
    assert expected==('error',msg),expected
    try: analyze_composed(W,acts,records)
    except ValueError as e: assert str(e)==msg,(str(e),msg)
    else: raise AssertionError(msg)
print('CONSTRUCTION_PASS controls=11 formal_seeds_used=0')
