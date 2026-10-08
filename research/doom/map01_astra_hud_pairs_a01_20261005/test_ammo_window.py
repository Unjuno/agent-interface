import unittest

from ammo_window_reconstruction import reconstruct


class AmmoWindowTests(unittest.TestCase):
    def setUp(self):
        self.report = {"decisions": []}
        for i, (source, commands, keys, start, end) in enumerate((
            ("117.png", [{"action":"fire"}], ["space"], 1_000_000_000, 2_000_000_000),
            ("148.png", [{"action":"turn_right"}], ["Right"], 3_000_000_000, 5_000_000_000),
            ("211.png", [], [], 6_000_000_000, 7_000_000_000),
        ), start=3):
            plan=f"plan-{i}-x"
            self.report["decisions"].append({
                "source_image": f"/runtime/{source}",
                "controller_model_started_ns":start,
                "controller_model_ended_ns":end,
                "action":{"commands":commands},
                "compiled_commands":commands,
                "execution_trace":[{"id":plan}],
            })
            if i==3: self.report["decisions"]=[{} for _ in range(3)]+self.report["decisions"]
        self.events=[]
        for seq,name,ts in ((117,"117.png",900_000_000),(148,"148.png",5_500_000_000),(211,"211.png",9_000_000_000)):
            self.events.append({"event":"observation","sequence":seq,"image":"/runtime/"+name,"capture_ns":ts,"exact":True})
        for plan, keys, verified_ns, terminal_ns in (("plan-3-x",["space"],5_597_000_000,5_597_100_000),("plan-4-x",["Right"],9_091_000_000,9_091_100_000)):
            self.events.append({"event":"keys_held","id":plan,"keys":keys})
            self.events.append({"event":"terminal","id":plan,"release":{"event":"owner_release","reason":"release","verified":True,"buttons_down":[],"keys_down":[],"verified_ns":verified_ns},"terminal_ns":terminal_ns})
        self.failure={"visual_transcription":{"ammo":[100,100,100,50,48,37]}}
        self.manifest={"frames":[]}
        self.frame_manifest=[{"iteration":i,"sha256":f"frame-{i}"} for i in range(13)]

    def test_reconstructs_ammo_drop_spanning_nonfire_plan(self):
        result=reconstruct(self.report,self.events,self.failure,self.manifest,self.frame_manifest,False)
        self.assertEqual([row["ammo_delta"] for row in result["windows"]],[-2,-11])
        self.assertEqual(result["windows"][1]["event_held_keys"],["Right"])
        self.assertEqual([row["owner_release"]["verified"] for row in result["windows"]],[True,True])
        self.assertAlmostEqual(result["windows"][1]["owner_release"]["capture_to_verified_release_ms"],91.0,places=6)
        self.assertEqual(result["disposition"],"PASS_POSTHOC_JOIN_HOLD_CAUSAL_ATTRIBUTION")

    def test_rejects_unverified_owner_release(self):
        terminal=next(row for row in self.events if row.get("event")=="terminal" and row.get("id")=="plan-4-x")
        terminal["release"]["verified"]=False
        with self.assertRaisesRegex(ValueError,"OWNER_RELEASE_RECEIPT_NOT_CLEAR"):
            reconstruct(self.report,self.events,self.failure,self.manifest,self.frame_manifest,False)

    def test_rejects_nonexact_endpoint(self):
        self.events[1]["exact"]=False
        with self.assertRaisesRegex(ValueError,"AMMO_ENDPOINT_NOT_EXACT"):
            reconstruct(self.report,self.events,self.failure,self.manifest,self.frame_manifest,False)


if __name__=="__main__":unittest.main()
