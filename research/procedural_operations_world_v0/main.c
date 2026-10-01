#define _POSIX_C_SOURCE 200809L
#include "ops_world.h"

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/keysym.h>
#include <errno.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec / 1e9;
}

static void sleep_ms(long ms) {
    struct timespec ts = {.tv_sec = ms / 1000, .tv_nsec = (ms % 1000) * 1000000L};
    while (nanosleep(&ts, &ts) && errno == EINTR) {}
}

static void usage(const char *argv0) {
    fprintf(stderr,
        "usage: %s [--seed N] [--family-key N] [--fixed] [--set key=value] [--report PATH]\n"
        "          [--dump-ppm PATH] [--headless-frames N] [--bench-frames N]\n"
        "          [--bench-resets N] [--runtime SEC] [--autoclose SEC]\n", argv0);
}

static int parse_set(OwDifficulty *d, const char *arg) {
    const char *eq = strchr(arg, '=');
    if (!eq) { fprintf(stderr, "invalid --set %s (expected key=value)\n", arg); return -1; }
    char key[64];
    size_t n = (size_t)(eq - arg);
    if (n == 0 || n >= sizeof(key)) return -1;
    memcpy(key, arg, n); key[n] = 0;
    const char *value = eq + 1;
    if (!*value) { fprintf(stderr, "invalid numeric value in --set %s\n", arg); return -1; }
    errno = 0;
    char *end = NULL;
    double v = strtod(value, &end);
    if (end == value || !end || *end || errno == ERANGE || !isfinite(v)) {
        fprintf(stderr, "invalid numeric value in --set %s\n", arg);
        return -1;
    }
    char err[160];
    if (ow_set_param(d, key, v, err, sizeof(err))) { fprintf(stderr, "%s\n", err); return -1; }
    return 0;
}

static int key_char(KeySym ks) {
    if (ks == XK_w || ks == XK_W) return 'w';
    if (ks == XK_a || ks == XK_A) return 'a';
    if (ks == XK_s || ks == XK_S) return 's';
    if (ks == XK_d || ks == XK_D) return 'd';
    if (ks == XK_Escape) return 27;
    return 0;
}

static int run_headless(OwWorld *w, OwFrame *frame, int frames, const char *ppm, const char *report, int bench) {
    double t0 = now_sec();
    int executed = 0;
    for (int i = 0; i < frames && !w->done; ++i) {
        ow_step(w, 1.0 / 60.0);
        ow_render(w, frame);
        ++executed;
    }
    if (frames == 0) ow_render(w, frame);
    double elapsed = now_sec() - t0;
    if (ppm && ow_write_ppm(ppm, frame)) { fprintf(stderr, "failed to write %s\n", ppm); return 2; }
    if (report && ow_report_json(w, report)) { fprintf(stderr, "failed to write %s\n", report); return 2; }
    if (bench) {
        double fps = elapsed > 0 ? executed / elapsed : 0.0;
        printf("bench_requested_frames=%d\nbench_executed_frames=%d\nwall_seconds=%.6f\nframes_per_second=%.2f\nms_per_frame=%.4f\nstate_hash=%016llx\n",
               frames, executed, elapsed, fps, elapsed * 1000.0 / (executed > 0 ? executed : 1),
               (unsigned long long)ow_state_hash(w));
    }
    return 0;
}

int main(int argc, char **argv) {
    uint64_t seed = 0;
    uint64_t family_key = 0;
    int seed_set = 0;
    int fixed = 0;
    int headless_frames = -1;
    int bench_frames = -1;
    int bench_resets = -1;
    double autoclose = -1.0;
    double runtime_limit = -1.0;
    const char *report = NULL;
    const char *ppm = NULL;
    OwDifficulty d;
    ow_default_difficulty(&d);

    for (int i = 1; i < argc; ++i) {
        if (!strcmp(argv[i], "--seed") && i + 1 < argc) { seed = strtoull(argv[++i], NULL, 10); seed_set = 1; }
        else if (!strcmp(argv[i], "--family-key") && i + 1 < argc) family_key = strtoull(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--fixed")) fixed = 1;
        else if (!strcmp(argv[i], "--set") && i + 1 < argc) { if (parse_set(&d, argv[++i])) return 2; }
        else if (!strcmp(argv[i], "--report") && i + 1 < argc) report = argv[++i];
        else if (!strcmp(argv[i], "--dump-ppm") && i + 1 < argc) ppm = argv[++i];
        else if (!strcmp(argv[i], "--headless-frames") && i + 1 < argc) headless_frames = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--bench-frames") && i + 1 < argc) bench_frames = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--bench-resets") && i + 1 < argc) bench_resets = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--runtime") && i + 1 < argc) runtime_limit = atof(argv[++i]);
        else if (!strcmp(argv[i], "--autoclose") && i + 1 < argc) autoclose = atof(argv[++i]);
        else { usage(argv[0]); return 2; }
    }
    char err[160];
    if (ow_validate_difficulty(&d, err, sizeof(err))) { fprintf(stderr, "%s\n", err); return 2; }
    if (!seed_set) {
        struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts);
        seed = ((uint64_t)ts.tv_sec << 32) ^ (uint64_t)ts.tv_nsec ^ (uint64_t)getpid();
    }

    OwWorld world;
    ow_init_with_family(&world, seed, family_key, &d);
    if (world.failure_code == OW_FAIL_EPISODE_GENERATION) {
        fprintf(stderr, "episode generation failed for seed/family/config\n");
        return 2;
    }
    if (bench_resets >= 0) {
        double t0 = now_sec();
        for (int i = 0; i < bench_resets; ++i) ow_init_with_family(&world, seed + (uint64_t)i, family_key, &d);
        double elapsed = now_sec() - t0;
        printf("bench_resets=%d\nwall_seconds=%.6f\nresets_per_second=%.2f\nus_per_reset=%.3f\n",
               bench_resets, elapsed, elapsed > 0 ? bench_resets/elapsed : 0.0,
               elapsed * 1e6 / (bench_resets > 0 ? bench_resets : 1));
        return 0;
    }
    OwFrame frame;
    frame.pixels = calloc((size_t)OW_WIDTH * OW_HEIGHT, sizeof(uint32_t));
    if (!frame.pixels) return 2;

    if (bench_frames >= 0) {
        int rc = run_headless(&world, &frame, bench_frames, ppm, report, 1);
        free(frame.pixels); return rc;
    }
    if (headless_frames >= 0) {
        int rc = run_headless(&world, &frame, headless_frames, ppm, report, 0);
        free(frame.pixels); return rc;
    }

    Display *display = XOpenDisplay(NULL);
    if (!display) { fprintf(stderr, "XOpenDisplay failed; use --headless-frames for no-X mode\n"); free(frame.pixels); return 2; }
    int screen = DefaultScreen(display);
    Window root = RootWindow(display, screen);
    Window win = XCreateSimpleWindow(display, root, 0, 0, OW_WIDTH, OW_HEIGHT, 0,
                                     BlackPixel(display, screen), BlackPixel(display, screen));
    XStoreName(display, win, "Procedural Operations World v0");
    XSelectInput(display, win, ExposureMask | KeyPressMask | KeyReleaseMask |
                              ButtonPressMask | ButtonReleaseMask | PointerMotionMask | StructureNotifyMask);
    Atom wm_delete = XInternAtom(display, "WM_DELETE_WINDOW", False);
    XSetWMProtocols(display, win, &wm_delete, 1);
    XMapWindow(display, win);

    XImage *img = XCreateImage(display, DefaultVisual(display, screen), DefaultDepth(display, screen),
                               ZPixmap, 0, (char*)frame.pixels, OW_WIDTH, OW_HEIGHT, 32, 0);
    if (!img) { XDestroyWindow(display, win); XCloseDisplay(display); free(frame.pixels); return 2; }
    GC gc = XCreateGC(display, win, 0, NULL);

    int running = 1, ignore_warp = 0;
    int last_x = OW_WIDTH/2, last_y = OW_HEIGHT/2;
    double last = now_sec(), done_at = -1.0, run_started = last;
    while (running) {
        while (XPending(display)) {
            XEvent ev; XNextEvent(display, &ev);
            if (ev.type == ClientMessage && (Atom)ev.xclient.data.l[0] == wm_delete) { running = 0; break; }
            if (ev.type == KeyPress) {
                KeySym ks = XLookupKeysym(&ev.xkey, 0);
                int kc = key_char(ks);
                if (kc) ow_key(&world, kc, 1);
                if (ks == XK_BackSpace) ow_backspace(&world);
                else if (ks == XK_Return || ks == XK_KP_Enter) ow_enter(&world);
                else {
                    char buf[8] = {0}; KeySym dummy; XComposeStatus cs;
                    int n = XLookupString(&ev.xkey, buf, sizeof(buf)-1, &dummy, &cs);
                    if (n == 1) ow_text(&world, buf[0]);
                }
            } else if (ev.type == KeyRelease) {
                KeySym ks = XLookupKeysym(&ev.xkey, 0); int kc = key_char(ks); if (kc && kc != 27) ow_key(&world, kc, 0);
            } else if (ev.type == MotionNotify) {
                int x = ev.xmotion.x, y = ev.xmotion.y;
                if (ignore_warp) { ignore_warp = 0; last_x = x; last_y = y; continue; }
                float dx = (float)(x - last_x), dy = (float)(y - last_y);
                ow_mouse_move(&world, dx, dy, (float)x, (float)y);
                last_x = x; last_y = y;
                if (!world.panel_open && y >= OW_HUD_H && (x < 5 || x > OW_WIDTH-6)) {
                    int nx = x < 5 ? OW_WIDTH-8 : 8;
                    ignore_warp = 1; XWarpPointer(display, None, win, 0,0,0,0,nx,y); XFlush(display);
                    last_x = nx; last_y = y;
                }
            } else if (ev.type == ButtonPress || ev.type == ButtonRelease) {
                int b = ev.xbutton.button == Button1 ? 1 : (ev.xbutton.button == Button3 ? 3 : ev.xbutton.button);
                ow_mouse_button(&world, b, ev.type == ButtonPress, (float)ev.xbutton.x, (float)ev.xbutton.y);
            }
        }
        double n = now_sec();
        double dt = fixed ? 1.0/60.0 : n - last;
        last = n;
        ow_step(&world, dt);
        ow_render(&world, &frame);
        XPutImage(display, win, gc, img, 0,0,0,0, OW_WIDTH, OW_HEIGHT);
        XFlush(display);
        if (world.done && done_at < 0) done_at = n;
        if (autoclose >= 0 && done_at >= 0 && n - done_at >= autoclose) running = 0;
        if (runtime_limit >= 0 && n - run_started >= runtime_limit) running = 0;
        sleep_ms(1);
    }
    if (ppm) ow_write_ppm(ppm, &frame);
    if (report) ow_report_json(&world, report);
    /* XImage owns frame.pixels after construction. */
    XDestroyImage(img);
    XFreeGC(display, gc); XDestroyWindow(display, win); XCloseDisplay(display);
    return 0;
}
