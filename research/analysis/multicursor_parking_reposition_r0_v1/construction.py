from model import *

def main():
    cases={
      'stationary':(2,2,2,2),
      'alternating_near':(0,1,0,1,0),
      'alternating_far':(0,3,0,3),
      'monotone':(0,1,2,3),
    }
    checks={}
    for name,seq in cases.items():
        checks[name+'_alias']=all(aliased_parked_cost(seq,k)==single_cost(seq) for k in (2,3,4))
        checks[name+'_formula']=all(single_cost(seq)-switch_cost(seq,s)==switch_gain_formula(seq,s) for s in range(4))
    checks['strict_gain']=switch_cost(cases['alternating_far'],1)<single_cost(cases['alternating_far'])
    checks['no_gain_when_s_ge_moves']=switch_cost(cases['monotone'],1)==single_cost(cases['monotone'])
    print(checks)
    assert all(checks.values())
if __name__=='__main__':main()
