from runner import schedules,ACTION_NS

def main():
    ss=schedules(1000,123)
    assert len(ss)==1000
    for s in ss:
        assert s['amb_start_ns']<s['amb_end_ns']<s['hard_start_ns']
        for t in (s['amb_start_ns'],s['amb_end_ns'],s['hard_start_ns']):
            assert t % ACTION_NS == ACTION_NS//2
    print('PASS static schedule tests')
if __name__=='__main__': main()
