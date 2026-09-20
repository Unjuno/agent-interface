#include <X11/Xlib.h>
#include <X11/extensions/XRes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static int x_error_code = 0;
static int capture_x_error(Display *display, XErrorEvent *event) {
    (void)display;
    x_error_code = event->error_code;
    fprintf(stderr, "XError code=%u request=%u minor=%u resource=%lu\n",
            event->error_code, event->request_code, event->minor_code,
            event->resourceid);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: xres_owner WINDOW_XID\n");
        return 2;
    }
    char *end = NULL;
    unsigned long parsed = strtoul(argv[1], &end, 0);
    if (!end || *end || parsed > UINT32_MAX) {
        fprintf(stderr, "invalid XID\n");
        return 2;
    }
    Display *display = XOpenDisplay(NULL);
    if (!display) {
        fprintf(stderr, "cannot open DISPLAY\n");
        return 3;
    }
    XSetErrorHandler(capture_x_error);
    int event_base = 0, error_base = 0;
    if (!XResQueryExtension(display, &event_base, &error_base)) {
        fprintf(stderr, "XRes extension unavailable\n");
        XCloseDisplay(display);
        return 4;
    }
    int major = 1, minor = 2;
    if (!XResQueryVersion(display, &major, &minor) || major < 1 ||
        (major == 1 && minor < 2)) {
        fprintf(stderr, "XRes 1.2 unavailable\n");
        XCloseDisplay(display);
        return 4;
    }
    int client_count = 0;
    XResClient *clients = NULL;
    if (!XResQueryClients(display, &client_count, &clients)) {
        fprintf(stderr, "XResQueryClients failed\n");
        XCloseDisplay(display);
        return 5;
    }
    XID resource_base = 0;
    XID resource_mask = 0;
    for (int i = 0; i < client_count; ++i) {
        XID base = clients[i].resource_base & ~clients[i].resource_mask;
        if (((XID)parsed & ~clients[i].resource_mask) == base) {
            resource_base = clients[i].resource_base;
            resource_mask = clients[i].resource_mask;
            break;
        }
    }
    XFree(clients);
    if (!resource_mask) {
        fprintf(stderr, "no XRes client owns XID\n");
        XCloseDisplay(display);
        return 6;
    }
    XResClientIdSpec spec = {(XID)parsed, XRES_CLIENT_ID_PID_MASK};
    long count = 0;
    XResClientIdValue *values = NULL;
    if (XResQueryClientIds(display, 1, &spec, &count, &values) != Success) {
        XSync(display, False);
        fprintf(stderr, "XResQueryClientIds failed for owner resource base=%lu mask=%lu error=%d\n",
                (unsigned long)resource_base, (unsigned long)resource_mask,
                x_error_code);
        XCloseDisplay(display);
        return 5;
    }
    pid_t owner_pid = -1;
    for (long i = 0; i < count; ++i) {
        if (values[i].spec.mask & XRES_CLIENT_ID_PID_MASK)
            owner_pid = XResGetClientPid(&values[i]);
    }
    if (owner_pid <= 0) {
        fprintf(stderr, "XRes LocalClientPID unavailable\n");
        free(values);
        XCloseDisplay(display);
        return 7;
    }
    printf("{\"xid\":%lu,\"client_base\":%lu,\"resource_mask\":%lu,"
           "\"pid\":%ld,\"xres_major\":%d,\"xres_minor\":%d}\n",
           parsed, (unsigned long)resource_base, (unsigned long)resource_mask,
           (long)owner_pid, major, minor);
    free(values);
    XCloseDisplay(display);
    return 0;
}
