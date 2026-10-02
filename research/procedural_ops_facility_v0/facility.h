#ifndef PROCEDURAL_OPS_FACILITY_H
#define PROCEDURAL_OPS_FACILITY_H

#include <stdint.h>
#include <stddef.h>

#define FACILITY_W 640
#define FACILITY_H 360
#define FACILITY_MAX_MAP 41
#define FACILITY_MAX_WATCHERS 12
#define FACILITY_MAX_TRACK_OBJECTS 16
#define FACILITY_MAX_ASSEMBLY 8
#define FACILITY_MAX_PATH (FACILITY_MAX_MAP * FACILITY_MAX_MAP)
#define FACILITY_CODE_MAX 24

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    PHASE_NAV = 0,
    PHASE_TERMINAL = 1,
    PHASE_ASSEMBLY = 2,
    PHASE_DONE = 3,
    PHASE_FAILED = 4
} FacilityPhase;

typedef enum {
    FAIL_NONE = 0,
    FAIL_EPISODE_DEADLINE,
    FAIL_WATCHER_DEADLINE,
    FAIL_TRACK_DEADLINE,
    FAIL_PREMATURE_ACTION,
    FAIL_STALE_ACTION,
    FAIL_WRONG_TARGET,
    FAIL_TYPING_ERROR,
    FAIL_ASSEMBLY_MISS
} FailureReason;

typedef struct {
    double level;
    int map_size;
    int maze_loops;
    int watcher_count;
    double watcher_event_rate_hz;
    int watcher_deadline_ticks;
    int track_distractors;
    double track_speed_px_per_tick;
    double track_target_radius_px;
    int track_event_interval_ticks;
    int track_deadline_ticks;
    int code_length;
    int assembly_pieces;
    double assembly_tolerance_px;
    double recovery_displacement_px;
    int episode_deadline_ticks;
    double fov_deg;
} Difficulty;

typedef struct {
    int active;
    int generation;
    int next_tick;
    int deadline_tick;
    int last_resolved_generation;
} Watcher;

typedef struct {
    double x;
    double y;
    double vx;
    double vy;
    int color;
    int shape;
} TrackObject;

typedef struct {
    double x;
    double y;
    double slot_x;
    double slot_y;
    int color;
    int shape;
    int placed;
} AssemblyPiece;

typedef struct {
    int forward;
    int back;
    int left;
    int right;
    double turn_delta;
    int ack_index;        /* -1 or [0, watcher_count) */
    int mouse_pressed;
    int mouse_down;
    int mouse_released;
    int mouse_x;
    int mouse_y;
    int typed_char;       /* ASCII or 0 */
    int enter;
} FacilityInput;

typedef struct {
    uint64_t seed;
    Difficulty d;
    uint64_t rng;
    int map_w;
    int map_h;
    uint8_t map[FACILITY_MAX_MAP][FACILITY_MAX_MAP];
    int start_cx;
    int start_cy;
    int terminal_cx;
    int terminal_cy;
    int path_x[FACILITY_MAX_PATH];
    int path_y[FACILITY_MAX_PATH];
    int path_len;

    double player_x;
    double player_y;
    double player_angle;
    double player_speed;

    FacilityPhase phase;
    FailureReason failure;
    int tick;
    int phase_tick;
    int done;
    int success;

    Watcher watchers[FACILITY_MAX_WATCHERS];
    int watcher_successes;
    int watcher_events;
    int watcher_deadline_misses;
    int premature_actions;
    int stale_actions;

    TrackObject track[FACILITY_MAX_TRACK_OBJECTS];
    int track_count;
    int track_authoritative;
    int track_previous_authoritative;
    int track_active;
    int track_generation;
    int track_next_event_tick;
    int track_deadline_tick;
    int track_successes;
    int track_events;
    int wrong_targets;

    char code[FACILITY_CODE_MAX + 1];
    char typed[FACILITY_CODE_MAX + 1];
    int typed_len;
    int terminal_focus;

    AssemblyPiece pieces[FACILITY_MAX_ASSEMBLY];
    int piece_count;
    int dragging_piece;
    int assembly_placed;
    int assembly_misses;
    int recovery_triggered;
    int recovery_events;
    int recovery_successes;

    uint64_t input_hash;
    uint64_t event_hash;
    uint64_t frame_hash;
} Facility;

typedef struct {
    int path_index;
    int typing_index;
    int assembly_index;
    int drag_state;
} ReferenceController;

Difficulty difficulty_from_level(double level);
int difficulty_set(Difficulty *d, const char *key, double value);
int facility_init(Facility *f, uint64_t seed, Difficulty d);
void facility_input_clear(FacilityInput *in);
void facility_step(Facility *f, const FacilityInput *in);
void facility_render(Facility *f, uint32_t *pixels, int width, int height);
uint64_t facility_state_hash(const Facility *f);
const char *facility_failure_name(FailureReason r);
const char *facility_phase_name(FacilityPhase p);
void reference_init(ReferenceController *r);
void reference_next(Facility *f, ReferenceController *r, FacilityInput *in);
int facility_write_report(const Facility *f, const char *path, double wall_seconds, uint64_t state_hash);
int facility_write_ppm(const uint32_t *pixels, int width, int height, const char *path);

#ifdef __cplusplus
}
#endif

#endif
