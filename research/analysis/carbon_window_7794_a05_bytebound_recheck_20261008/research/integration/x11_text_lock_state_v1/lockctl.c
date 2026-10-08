#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <X11/keysym.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

int main(int argc, char **argv) {
    if (argc != 3 || argv[1][0] != ':') return 2;
    if (strcmp(argv[2], "0") && strcmp(argv[2], "1") && strcmp(argv[2], "query")) return 2;
    Display *d = XOpenDisplay(argv[1]);
    if (!d) return 3;
    if (strcmp(argv[2], "query")) {
        if (!XkbLockModifiers(d, XkbUseCoreKbd, LockMask, !strcmp(argv[2], "1") ? LockMask : 0)) return 4;
        XSync(d, False);
    }
    XkbStateRec s;
    if (XkbGetState(d, XkbUseCoreKbd, &s) != Success) return 5;
    char keys[32];
    XQueryKeymap(d, keys);
    Window rr, child, focus;
    int rx, ry, wx, wy, revert;
    unsigned int mask;
    if (!XQueryPointer(d, DefaultRootWindow(d), &rr, &child, &rx, &ry, &wx, &wy, &mask)) return 6;
    XGetInputFocus(d, &focus, &revert);
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    printf("{\"locked\":%u,\"base\":%u,\"latched\":%u,\"group\":%u,\"mask\":%u,\"focus\":%lu,\"ns\":%lld,\"keymap\":\"",
           s.locked_mods, s.base_mods, s.latched_mods, s.group, mask, focus,
           (long long)t.tv_sec * 1000000000LL + t.tv_nsec);
    for (int i=0; i<32; i++) printf("%02x", (unsigned char)keys[i]);
    printf("\",\"codes\":[%u,%u,%u,%u]}\n", XKeysymToKeycode(d,XK_a),
           XKeysymToKeycode(d,XK_b), XKeysymToKeycode(d,XK_2), XKeysymToKeycode(d,XK_Shift_L));
    XCloseDisplay(d);
    return 0;
}
