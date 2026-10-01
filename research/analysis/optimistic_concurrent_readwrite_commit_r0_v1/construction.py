from model import candidate, write_only, PARALLEL, SERIALIZE, REVALIDATE
from oracle import oracle


def main():
    checks = {}
    row=(1<<0, 1<<1, 1<<2, 1<<3, 0)
    checks['disjoint_parallel'] = candidate(*row) == PARALLEL == oracle(*row)
    row=((1<<0), (1<<1), (1<<0), (1<<2), 0)
    checks['read_read_ok'] = candidate(*row) == PARALLEL == oracle(*row)
    row=(1<<0, 0, 0, 0, 1<<0)
    checks['stale_read_revalidate'] = candidate(*row) == REVALIDATE == oracle(*row)
    row=(0,1<<0,1<<0,0,0)
    checks['a_write_b_read_serial'] = candidate(*row) == SERIALIZE == oracle(*row)
    checks['write_only_misses_a_write_b_read'] = write_only(*row) == PARALLEL
    row=(1<<1,0,0,1<<1,0)
    checks['b_write_a_read_serial'] = candidate(*row) == SERIALIZE == oracle(*row)
    checks['write_only_misses_b_write_a_read'] = write_only(*row) == PARALLEL
    row=(0,1<<2,0,1<<2,0)
    checks['ww_serial'] = candidate(*row) == SERIALIZE == oracle(*row)
    row=(1<<0,1<<1,1<<2,1<<3,0)
    checks['same_surface_disjoint_positive'] = candidate(*row) == PARALLEL
    g=1<<3
    row=(0,g,g,0,0)
    checks['different_surface_shared_global_negative'] = candidate(*row) == SERIALIZE
    bad=0
    for row in [(-1,0,0,0,0),(16,0,0,0,0),(0,0,0,0,17)]:
        try: candidate(*row)
        except ValueError: bad += 1
    checks['malformed_rejected'] = bad == 3
    print(checks)
    assert all(checks.values())

if __name__ == '__main__':
    main()
