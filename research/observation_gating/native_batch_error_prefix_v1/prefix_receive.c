/* Research-only AF_UNIX datagram adapter. Prefix and error are separate outputs. */
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
int read_prefix(int fd, unsigned char *buffer, size_t bytes, int *lengths,
                uint64_t *dequeued_ns, uint64_t *clocks,
                int *fault_errno, uint64_t *rejected_size) {
    if (fd<0 || !buffer || bytes!=64*8192 || !lengths || !dequeued_ns ||
        !clocks || !fault_errno || !rejected_size) return -EINVAL;
    *fault_errno=0; *rejected_size=0;
    clocks[0]=now_ns();
    struct pollfd p={fd,POLLIN,0};
    int ready=poll(&p,1,20);
    int count=0;
    if (ready<0) {
        *fault_errno=errno;
        clocks[1]=now_ns();
        return 0;
    }
    if (ready>0) {
        uint64_t deadline=now_ns()+2000000ULL;
        for (int i=0;i<64;i++) {
            ssize_t n=recv(fd,buffer+(size_t)i*8192,8192,MSG_DONTWAIT|MSG_TRUNC);
            if (n<0) {
                if (errno!=EAGAIN && errno!=EWOULDBLOCK && errno!=EINTR)
                    *fault_errno=errno;
                break;
            }
            if (n>8192) {
                *fault_errno=EMSGSIZE; *rejected_size=(uint64_t)n;
                break;
            }
            lengths[count]=(int)n;
            dequeued_ns[count]=now_ns();
            count++;
            if (dequeued_ns[count-1]>=deadline) break;
        }
    }
    clocks[1]=now_ns();
    return count;
}
