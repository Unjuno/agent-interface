#ifndef OPS_WORLD_H
#define OPS_WORLD_H

#include <stdint.h>
#include <stddef.h>

#define OW_WIDTH 640
#define OW_HEIGHT 360
#define OW_MAP_W 20
#define OW_MAP_H 20
#define OW_MAX_WATCHERS 64
#define OW_MAX_OBJECTS 64
#define OW_MAX_STATIONS 8
#define OW_MAX_ASSEMBLY 12
#define OW_MAX_EVENTS 4096
#define OW_MAX_ALERT_SCHEDULE 512
#define OW_CODE_MAX 24
#define OW_HUD_H 54

#define OW_TASK_TRANSFER 0x01u
#define OW_TASK_ASSEMBLY 0x02u
#define OW_TASK_TARGET   0x04u
#define OW_TASK_ALERTS   0x08u

typedef enum {
    OW_STATION_SOURCE = 0,
    OW_STATION_TERMINAL = 1,
    OW_STATION_ASSEMBLY = 2,
    OW_STATION_MONITOR = 3,
} OwStationKind;

typedef enum {
    OW_FAIL_NONE = 0,
    OW_FAIL_EPISODE_TIMEOUT = 1,
    OW_FAIL_MISSED_ALERT = 2,
    OW_FAIL_FORBIDDEN_ACTION = 3,
    OW_FAIL_MOTOR_MISS = 4,
    OW_FAIL_TERMINAL_BAD = 5,
    OW_FAIL_ASSEMBLY_MISS = 6,
    OW_FAIL_RECOVERY_EXHAUSTED = 7,
    OW_FAIL_EPISODE_GENERATION = 8,
    OW_FAIL_EVENT_OVERFLOW = 100,
} OwFailureCode;

typedef struct {
    float target_speed;
    float object_radius;
    int object_count;
    int watcher_count;
    float event_rate;          /* total alert arrivals / simulated second */
    float alert_deadline;
    int alert_burst;           /* simultaneous alerts per opportunity */
    int required_alerts;
    int typing_length;
    int assembly_pieces;
    float assembly_tolerance;
    float navigation_speed;
    float mouse_gain;
    float episode_seconds;
    int work_task_count;       /* selected from transfer/assembly/target */
    int dependency_depth;      /* 0=parallel, 1=one dependency, 2=chain */
    int recovery_budget;       /* recoverable mistakes before hard failure */
} OwDifficulty;

typedef struct {
    float x, y;
    float vx, vy;
    uint8_t color;
    uint8_t shape;
    uint8_t target;
    uint8_t active;
} OwObject;

typedef struct {
    float x, y;
    uint8_t kind;
    uint8_t color;
    uint8_t icon_style;
} OwStation;

typedef struct {
    double next_event;         /* evaluator/debug metadata only */
    double deadline;
    double ack_flash_until;
    uint32_t generation;
    uint8_t alert;
    uint8_t acknowledged;
} OwWatcher;

typedef struct {
    float x, y;
    float home_x, home_y;
    float slot_x, slot_y;
    uint8_t color;
    uint8_t shape;
    uint8_t placed;
} OwPiece;

typedef struct {
    double t;
    uint8_t watcher;
    uint8_t burst_slot;
} OwScheduledAlert;

typedef struct {
    double t;
    uint16_t type;
    int16_t a;
    int16_t b;
    float x;
    float y;
} OwEvent;

typedef struct {
    uint64_t seed;
    uint64_t family_key;       /* evaluator-private generation/presentation nonce */
    uint64_t episode_hash;     /* immutable generated episode fingerprint */
    OwDifficulty d;
    uint8_t map[OW_MAP_H][OW_MAP_W];
    uint8_t map_variant;
    uint16_t map_openings_mask;
    uint8_t presentation_family;

    uint8_t task_mask;
    uint8_t task_order[3];
    uint8_t task_deps[3];      /* indexed transfer=0, assembly=1, target=2 */
    uint8_t task_graph_variant;

    float px, py, angle;
    uint8_t key_w, key_a, key_s, key_d;
    uint8_t panel_open;
    int active_station;

    OwStation stations[OW_MAX_STATIONS];
    int station_count;
    OwObject objects[OW_MAX_OBJECTS];
    int object_count;
    int target_object;
    float target_reloc_x, target_reloc_y;
    OwWatcher watchers[OW_MAX_WATCHERS];
    int watcher_count;
    OwScheduledAlert alert_schedule[OW_MAX_ALERT_SCHEDULE];
    int alert_schedule_count;
    int alert_schedule_cursor;
    OwPiece pieces[OW_MAX_ASSEMBLY];
    int piece_count;

    char source_code[OW_CODE_MAX];
    char typed_code[OW_CODE_MAX];
    int typed_len;
    uint8_t terminal_complete;
    uint8_t assembly_complete;
    uint8_t target_complete;
    int target_hits;
    int target_hits_required;
    int alerts_spawned;
    int alerts_acked;
    int alerts_missed;

    int drag_piece;
    float cursor_x, cursor_y;

    double sim_time;
    double started_wall;
    double max_step_dt;
    uint64_t step_calls;
    uint64_t internal_steps;
    uint8_t done;
    uint8_t success;
    uint16_t failure_code;

    uint64_t actions;
    uint64_t key_events;
    uint64_t pointer_events;
    uint64_t wrong_actions;
    uint64_t motor_misses;
    uint64_t false_acks;
    uint64_t recoverable_errors;
    uint64_t recoveries;
    uint8_t pending_recovery;

    OwEvent events[OW_MAX_EVENTS];
    int event_count;
    uint8_t event_overflow;

    uint64_t rng_state;
} OwWorld;

typedef struct {
    uint32_t *pixels;
    float zbuf[OW_WIDTH];
} OwFrame;

void ow_default_difficulty(OwDifficulty *d);
int ow_set_param(OwDifficulty *d, const char *key, double value, char *err, size_t errcap);
int ow_validate_difficulty(const OwDifficulty *d, char *err, size_t errcap);
void ow_init(OwWorld *w, uint64_t seed, const OwDifficulty *d);
void ow_init_with_family(OwWorld *w, uint64_t seed, uint64_t family_key, const OwDifficulty *d);
void ow_step(OwWorld *w, double dt);
void ow_key(OwWorld *w, int key, int down);
void ow_text(OwWorld *w, char ch);
void ow_backspace(OwWorld *w);
void ow_enter(OwWorld *w);
void ow_mouse_move(OwWorld *w, float dx, float dy, float x, float y);
void ow_mouse_button(OwWorld *w, int button, int down, float x, float y);
void ow_watcher_tile_rect(const OwWorld *w, int idx, int *x, int *y, int *tw, int *th);
void ow_render(OwWorld *w, OwFrame *f);
int ow_write_ppm(const char *path, const OwFrame *f);
int ow_report_json(const OwWorld *w, const char *path);
uint64_t ow_state_hash(const OwWorld *w);

#endif
