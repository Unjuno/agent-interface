/* Research-only full-ROI XGetImage adapter. No shared memory or subsampling. */
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <stddef.h>
#include <string.h>

int q_init(void) { return XInitThreads(); }
void *q_open(const char *name) { return XOpenDisplay(name); }
void q_close(void *p) { if (p) XCloseDisplay((Display *)p); }
int q_read(void *p, unsigned char *out, size_t capacity) {
    if (!p || !out || capacity != 4096) return -1;
    Display *d = (Display *)p;
    XImage *im = XGetImage(d, DefaultRootWindow(d), 48, 48, 32, 32,
                           0xffffffffUL, ZPixmap);
    if (!im) return -2;
    int valid = im->width == 32 && im->height == 32 && im->depth == 24 &&
        im->bits_per_pixel == 32 && im->bytes_per_line == 128 &&
        im->byte_order == LSBFirst && im->red_mask == 0xff0000UL &&
        im->green_mask == 0x00ff00UL && im->blue_mask == 0x0000ffUL;
    if (valid) memcpy(out, im->data, 4096);
    XDestroyImage(im);
    return valid ? 0 : -3;
}
