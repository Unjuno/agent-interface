#include "facility.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static Facility fresh(uint64_t seed) {
    Facility f;
    Difficulty d = difficulty_from_level(0.45);
    assert(facility_init(&f, seed, d) == 0);
    return f;
}

static void test_premature_watcher_ack(void) {
    Facility f = fresh(101);
    FacilityInput in; facility_input_clear(&in);
    in.ack_index = 0;
    facility_step(&f, &in);
    assert(f.done && !f.success);
    assert(f.failure == FAIL_PREMATURE_ACTION);
}

static void test_stale_watcher_ack(void) {
    Facility f = fresh(102);
    f.watchers[0].active = 1;
    f.watchers[0].generation = 1;
    f.watchers[0].deadline_tick = f.tick + 100;
    FacilityInput in; facility_input_clear(&in);
    in.ack_index = 0;
    facility_step(&f, &in);
    assert(!f.done);
    assert(f.watcher_successes == 1);
    facility_input_clear(&in);
    in.ack_index = 0;
    facility_step(&f, &in);
    assert(f.done && !f.success);
    assert(f.failure == FAIL_STALE_ACTION);
}

static void test_wrong_track_target(void) {
    Facility f = fresh(103);
    assert(f.track_count >= 2);
    f.track_authoritative = 0;
    f.track_previous_authoritative = -1;
    f.track_active = 1;
    f.track_deadline_tick = f.tick + 100;
    f.track[0].x = 20; f.track[0].y = 20; f.track[0].vx = f.track[0].vy = 0;
    f.track[1].x = 120; f.track[1].y = 70; f.track[1].vx = f.track[1].vy = 0;
    FacilityInput in; facility_input_clear(&in);
    in.mouse_pressed = 1;
    in.mouse_x = FACILITY_W - 174 + 120;
    in.mouse_y = FACILITY_H - 114 + 70;
    facility_step(&f, &in);
    assert(f.done && !f.success);
    assert(f.failure == FAIL_WRONG_TARGET);
    assert(f.wrong_targets == 1);
}

static void test_typing_error(void) {
    Facility f = fresh(104);
    f.phase = PHASE_TERMINAL;
    f.phase_tick = 0;
    strcpy(f.code, "ABC");
    f.typed_len = 0; f.typed[0] = '\0';
    FacilityInput in; facility_input_clear(&in);
    in.typed_char = 'X'; facility_step(&f, &in);
    facility_input_clear(&in); in.enter = 1; facility_step(&f, &in);
    assert(f.done && !f.success);
    assert(f.failure == FAIL_TYPING_ERROR);
}

static void test_assembly_miss(void) {
    Facility f = fresh(105);
    f.phase = PHASE_ASSEMBLY;
    f.phase_tick = 0;
    f.piece_count = 1;
    f.pieces[0].x = 80; f.pieces[0].y = 160;
    f.pieces[0].slot_x = 500; f.pieces[0].slot_y = 200;
    f.pieces[0].placed = 0;
    f.dragging_piece = -1;
    FacilityInput in; facility_input_clear(&in);
    in.mouse_pressed = 1; in.mouse_down = 1; in.mouse_x = 80; in.mouse_y = 160;
    facility_step(&f, &in);
    assert(f.dragging_piece == 0);
    facility_input_clear(&in); in.mouse_down = 1; in.mouse_x = 120; in.mouse_y = 160;
    facility_step(&f, &in);
    facility_input_clear(&in); in.mouse_released = 1; in.mouse_x = 120; in.mouse_y = 160;
    facility_step(&f, &in);
    assert(f.done && !f.success);
    assert(f.failure == FAIL_ASSEMBLY_MISS);
}

static void test_difficulty_validation(void) {
    Difficulty d = difficulty_from_level(0.5);
    assert(difficulty_set(&d, "watcher_count", 6) == 0);
    assert(d.watcher_count == 6);
    assert(difficulty_set(&d, "watcher_count", 99) != 0);
    assert(difficulty_set(&d, "assembly_tolerance_px", 0) != 0);
    assert(difficulty_set(&d, "not_a_real_axis", 1) != 0);
}

int main(void) {
    test_premature_watcher_ack();
    test_stale_watcher_ack();
    test_wrong_track_target();
    test_typing_error();
    test_assembly_miss();
    test_difficulty_validation();
    puts("CORE_TESTS_PASS 6");
    return 0;
}
