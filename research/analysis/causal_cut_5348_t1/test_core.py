"""Construction tests; graph checks are independent of vector-cut candidate."""
import unittest
from causal_core import *
def graph_closed(events,cut):
 ids={e["id"] for e in events if e["seq"]<=cut[e["process"]]};by={e["id"]:e for e in events};todo=list(ids)
 while todo:
  e=by[todo.pop()]
  for p in e["parents"]:
   if p not in ids:return False
   todo.append(p)
 return True
class CutTests(unittest.TestCase):
 def test_every_prefix_cut_matches_independent_graph_closure(self):
  for name,events in topologies().items():
   maxima={p:max([e["seq"] for e in events if e["process"]==p],default=0) for p in PROCESSES}
   for a in range(maxima["A"]+1):
    for b in range(maxima["B"]+1):
     cut={"A":a,"B":b};selected=selected_events(events,cut)
     if selected:self.assertEqual(all(all(p in {e["id"] for e in selected} for p in e["parents"]) for e in selected),graph_closed(events,cut),name+str(cut))
 def test_receive_without_send_is_not_certified(self):self.assertEqual(classify(topologies()["cross_ack"],{"A":0,"B":2}),"INCOMPLETE_IN_FLIGHT")
 def test_complete_cross_ack_is_consistent(self):self.assertEqual(classify(topologies()["cross_ack"],{"A":2,"B":3}),"CONSISTENT")
 def test_unmatched_send_is_incomplete_even_with_channel_marker(self):
  e=topologies()["cross_ack"];self.assertEqual(classify(e,{"A":1,"B":1},{"m1":"IN_FLIGHT"}),"INCOMPLETE_IN_FLIGHT");self.assertEqual(classify(e,{"A":1,"B":1},{"m1":"DROPPED"}),"INCOMPLETE_IN_FLIGHT")
 def test_missing_metadata_is_unknown(self):self.assertEqual(classify(topologies()["cross_ack"],{"A":1,"B":1},{},False),"UNKNOWN")
 def test_out_of_order_delivery_complete_cut_is_admitted(self):self.assertEqual(classify(topologies()["reordered_delivery"],{"A":2,"B":2}),"CONSISTENT")
 def test_independent_concurrent_cut_is_admitted(self):self.assertEqual(classify(topologies()["independent_concurrent"],{"A":1,"B":1}),"CONSISTENT")
 def test_conflicting_duplicate_is_contradictory(self):
  r=next(x for x in build_raw()["rows"] if x["case"]=="conflicting_duplicate_delivery");self.assertEqual(r["decision"],"CONTRADICTORY")
 def test_identical_duplicate_is_dedup_safe(self):
  r=next(x for x in build_raw()["rows"] if x["case"]=="identical_duplicate_delivery");self.assertEqual(r["decision"],"CONSISTENT");self.assertEqual(len(set(r["selected_event_ids"])),3)
 def test_freshness_only_admits_an_inconsistent_bundle(self):
  r=next(x for x in build_raw()["rows"] if x["case"]=="cross_ack" and x["cut"]=={"A":0,"B":2});self.assertTrue(r["per_record_freshness_admits"]);self.assertFalse(r["certified_cross_source_claim"])
 def test_no_side_effect_capability_in_raw(self):self.assertEqual(build_raw()["side_effects"],{"authority_grants":0,"actions_dispatched":0,"network_calls":0,"model_calls":0,"gpu_calls":0})
if __name__=="__main__":unittest.main()
