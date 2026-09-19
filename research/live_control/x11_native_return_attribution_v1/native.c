/* Research-only XGetImage timing probe; no user input or shared runtime. */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <time.h>

static uint64_t ns(clockid_t c) {
    struct timespec t;
    if (clock_gettime(c, &t)) return 0;
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}
int q_init(void) { return XInitThreads(); }
void *q_open(const char *s) { return XOpenDisplay(s); }
void q_close(void *p) { if (p) XCloseDisplay((Display *)p); }
/* q_read trace: C entry, XGetImage before, after, C exit, X CPU before/after. */
int q_read(void *p, unsigned char *out, size_t n, uint64_t *t) {
    if (!p || !out || n != 4096 || !t) return -1;
    t[0] = ns(CLOCK_MONOTONIC);
    Display *d = (Display *)p;
    t[4] = ns(CLOCK_THREAD_CPUTIME_ID);
    t[1] = ns(CLOCK_MONOTONIC);
    XImage *im = XGetImage(d, DefaultRootWindow(d), 48, 48, 32, 32,
                         0xffffffffUL, ZPixmap);
    t[2] = ns(CLOCK_MONOTONIC);
    t[5] = ns(CLOCK_THREAD_CPUTIME_ID);
    if (!im) return -2;
    int ok = im->width == 32 && im->height == 32 && im->depth == 24 &&
        im->bits_per_pixel == 32 && im->bytes_per_line == 128 &&
        im->byte_order == LSBFirst && im->red_mask == 0xff0000UL &&
        im->green_mask == 0x00ff00UL && im->blue_mask == 0x0000ffUL;
    if (ok) memcpy(out, im->data, 4096);
    XDestroyImage(im);
    t[3] = ns(CLOCK_MONOTONIC);
    return ok ? 0 : -3;
}
/* Fixture setup only; render exact n target pixels, not an input action. */
int q_paint(void *p, int n) {
    if (!p || n < 0 || n > 1024) return -1;
    Display *d = (Display *)p;
    Window w = DefaultRootWindow(d);
    GC g = XCreateGC(d, w, 0, NULL);
    XSetForeground(d, g, 0x101010UL);
    XFillRectangle(d, w, g, 48, 48, 32, 32);
    XSetForeground(d, g, 0xdc3232UL);
    for (int i = 0; i < n; ++i) XDrawPoint(d, w, g, 48 + i % 32, 48 + i / 32);
    XFreeGC(d, g); XSync(d, False);
    return 0;
}
/* Construction-only cross-language clock enclosure control. */
int q_pause(uint64_t *t) {
    if (!t) return -1;
    struct timespec delay = {0, 2000000};
    t[0] = ns(CLOCK_MONOTONIC);
    while (nanosleep(&delay, &delay)) { }
    t[1] = ns(CLOCK_MONOTONIC);
    return 0;
}
