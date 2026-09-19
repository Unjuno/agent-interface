import random
import formal_runner as f
m=f.load_candidate(); r=random.Random(123456789)
for i in range(200):
    c=f.generate_case(r,i)
    assert f.candidate_eval(m,c)==f.oracle(c)
assert all(f.run_controls(m).values())
print('PASS excluded construction cases=200 controls=9')
