import importlib.util, unittest
from pathlib import Path

p = Path(__file__).with_name("setup.py")
s = importlib.util.spec_from_file_location("fss_setup", p)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)

class Construction(unittest.TestCase):
    def test_lamport_sign_verify_and_mutation(self):
        seed = bytes(range(32)); msg = b"fixture"
        pub = m.ots_public(seed); sig = m.ots_sign(seed, msg)
        self.assertTrue(m.ots_verify(pub, msg, sig))
        self.assertFalse(m.ots_verify(pub, b"different", sig))
    def test_merkle_proofs_all_leaves(self):
        pubs = [m.ots_public(bytes([i])*32) for i in range(8)]
        levels = m.merkle_levels(pubs); root = m.hx(levels[-1][0])
        for i,pub in enumerate(pubs):
            node=m.leaf_hash(pub); idx=i
            for step in m.proof(levels,i):
                sib=bytes.fromhex(step["hash"])
                node=m.sha(b"NODE1" + (sib+node if step["side"]=="L" else node+sib)); idx//=2
            self.assertEqual(m.hx(node),root)
    def test_frontier_discards_prior_secrets(self):
        root=bytes(range(32)); frontier=[(0,8,root)]; consumed=[]
        for _ in range(7):
            secret,frontier=m.frontier_consume(frontier); consumed.append(secret)
        self.assertEqual([x[0] for x in frontier],[7])
        self.assertEqual(frontier[0][1],1)
        self.assertNotIn(frontier[0][2],consumed)
    def test_body_head_binding(self):
        a={"period":1,"claim":"x","previous_head":"00"*32}
        b={"period":1,"claim":"y","previous_head":"00"*32}
        self.assertNotEqual(m.head_for("00"*32,a),m.head_for("00"*32,b))

if __name__ == "__main__": unittest.main(verbosity=2)
