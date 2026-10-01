import pathlib,unittest
HERE=pathlib.Path(__file__).resolve().parent
class Static(unittest.TestCase):
    def test_builder_pins_dependencies_and_generated_blob(self):
        s=(HERE/'build_precise.py').read_text()
        for token in ['157a240147dfed2f8dfae553e090dbe24db832f2','565494630e48b3fa95eb89daa8e852f9b7094159','a766205e0c75288e3583f45ba2b58b58f7aca951']:
            self.assertIn(token,s)
    def test_fixed_schedule(self):
        s=(HERE/'run_schedule.py').read_text().replace(' ','')
        self.assertIn('[[0.8,0.9,1.0,1.1],[1.1,1.0,0.9,0.8],[0.9,1.1,0.8,1.0],[1.0,0.8,1.1,0.9],[1.1,0.9,1.0,0.8]]',s)
    def test_five_of_five_gate(self):
        s=(HERE/'aggregate.py').read_text(); self.assertIn("eligible_sessions']==ROUNDS",s); self.assertIn("exact_sessions']==ROUNDS",s)
    def test_dependency_runner_read_only(self):
        s=(HERE/'run_schedule.py').read_text(); self.assertIn("runtime_native_x11_text_pacing_v1",s); self.assertNotIn('write_text(',s.split('RUN_ARM=')[0])
if __name__=='__main__': unittest.main()
