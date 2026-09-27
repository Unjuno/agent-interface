#include "../src/facility.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static Facility make_facility(uint64_t seed, double d) {
    Facility f;
    FacilityConfig c = facility_config_from_difficulty(d);
    facility_init(&f, seed, &c);
    return f;
}

int main(void) {
    Facility a = make_facility(1234, 0.5);
    Facility b = make_facility(1234, 0.5);
    Facility c = make_facility(1235, 0.5);
    assert(a.spec_hash == b.spec_hash);
    assert(a.spec_hash != c.spec_hash);

    Facility p = make_facility(88, 0.0);
    assert(!p.done);
    facility_key_down(&p, "F1");
    assert(p.done && !p.success);
    assert(strcmp(p.failure_reason, "premature_ack") == 0);

    Facility w = make_facility(99, 0.0);
    w.cfg.strict_inhibition = false;
    int active_tick = w.watchers[0].active_tick;
    facility_step(&w, active_tick);
    assert(w.watchers[0].state == WATCH_ACTIVE);
    facility_key_down(&w, "F1");
    assert(w.metrics.watcher_acks == 1);

    Facility d = make_facility(77, 0.0);
    d.panel = PANEL_DEST;
    facility_text(&d, "WRONG");
    facility_key_down(&d, "ENTER");
    assert(d.done && !d.success);
    assert(strcmp(d.failure_reason, "wrong_code") == 0);

    Facility m = make_facility(66, 0.0);
    m.panel = PANEL_ASSEMBLY;
    facility_pointer_down(&m, m.piece_x[0], m.piece_y[0]);
    facility_pointer_move(&m, 150, 150);
    facility_pointer_up(&m, 150, 150);
    assert(m.done && !m.success);
    assert(strcmp(m.failure_reason, "assembly_miss") == 0);

    FacilityConfig cfg = facility_config_from_difficulty(0.5);
    char err[128];
    assert(!facility_config_set(&cfg, "watcher_count=99", err, sizeof(err)));
    assert(!facility_config_set(&cfg, "assembly_tolerance_px=0", err, sizeof(err)));
    assert(!facility_config_set(&cfg, "unknown_axis=1", err, sizeof(err)));
    assert(facility_config_set(&cfg, "watcher_count=7", err, sizeof(err)));
    assert(cfg.watcher_count == 7);

    printf("CORE_TEST_PASS\n");
    return 0;
}
