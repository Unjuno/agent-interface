#define _GNU_SOURCE
#include <errno.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/syscall.h>

/* Construction-only diagnostic: stamp stdout writes from engine and Python
 * with the same kernel CLOCK_MONOTONIC used by Python time.monotonic_ns(). */
ssize_t write(int fd, const void *buffer, size_t count) {
    if (fd != STDOUT_FILENO || count > 131000) {
        return (ssize_t)syscall(SYS_write, fd, buffer, count);
    }

    static pthread_mutex_t guard = PTHREAD_MUTEX_INITIALIZER;
    pthread_mutex_lock(&guard);
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
        int saved = errno;
        pthread_mutex_unlock(&guard);
        errno = saved;
        return -1;
    }
    uint64_t mono_ns = (uint64_t)now.tv_sec * UINT64_C(1000000000) +
                       (uint64_t)now.tv_nsec;
    char prefix[64];
    int prefix_len = snprintf(prefix, sizeof(prefix),
                              "CLOCK_MONOTONIC_NS=%llu ",
                              (unsigned long long)mono_ns);
    if (prefix_len <= 0 || (size_t)prefix_len >= sizeof(prefix)) {
        pthread_mutex_unlock(&guard);
        errno = EIO;
        return -1;
    }

    static char combined[131072];
    memcpy(combined, prefix, (size_t)prefix_len);
    memcpy(combined + prefix_len, buffer, count);
    ssize_t written = (ssize_t)syscall(SYS_write, fd, combined,
                                       (size_t)prefix_len + count);
    pthread_mutex_unlock(&guard);
    if (written < prefix_len) return written < 0 ? written : 0;
    return written - prefix_len;
}
