/* Research-only bounded receive batching; no pixel policy or input authority. */
#define _POSIX_C_SOURCE 200809L
#include <sys/socket.h>
#include <poll.h>
#include <stdint.h>
#include <errno.h>
#include <time.h>
#include <stddef.h>
static uint64_t now_ns(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return 0;
    return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
int read_batch(int fd, unsigned char *buffer, size_t bytes, int *lengths,
               uint64_t *dequeued_ns, uint64_t *clocks) {
    if (fd<0 || !buffer || bytes!=64*8192 || !lengths || !dequeued_ns || !clocks) return -EINVAL;
    clocks[0]=now_ns();
    struct pollfd p={fd,POLLIN,0};
    int ready=poll(&p,1,20);
    if (ready<0) {clocks[1]=now_ns();return errno==EINTR ? 0 : -errno;}
    int count=0;
    if (ready>0) {
        uint64_t deadline=now_ns()+2000000ULL;
        for (int i=0;i<64;i++) {
            ssize_t n=recv(fd,buffer+(size_t)i*8192,8192,MSG_DONTWAIT|MSG_TRUNC);
            if (n<0) {
                if (errno==EAGAIN || errno==EWOULDBLOCK || errno==EINTR) break;
                clocks[1]=now_ns();return -errno;
            }
            if (n>8192) {clocks[1]=now_ns();return -EMSGSIZE;}
            lengths[count]=(int)n;
            dequeued_ns[count]=now_ns();
            count++;
            if (dequeued_ns[count-1]>=deadline) break;
        }
    }
    clocks[1]=now_ns();
    return count;
}
