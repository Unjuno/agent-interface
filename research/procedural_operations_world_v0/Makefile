CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Wpedantic
LDLIBS ?= -lm -lX11

.PHONY: all test clean smoke
all: ops_world test_ops_world render_fixtures

ops_world: main.o ops_world.o
	$(CC) $(CFLAGS) -o $@ $^ $(LDLIBS)

test_ops_world: test_ops_world.o ops_world.o
	$(CC) $(CFLAGS) -o $@ $^ -lm

render_fixtures: render_fixtures.o ops_world.o
	$(CC) $(CFLAGS) -o $@ $^ -lm

main.o: main.c ops_world.h
ops_world.o: ops_world.c ops_world.h ops_world_part_00.inc ops_world_part_01.inc ops_world_part_02.inc ops_world_part_03.inc
test_ops_world.o: test_ops_world.c ops_world.h
render_fixtures.o: render_fixtures.c ops_world.h

test: test_ops_world
	./test_ops_world

smoke: all
	./test_ops_world
	./ops_world --seed 20260928 --headless-frames 120 --dump-ppm /tmp/ops-world.ppm --report /tmp/ops-world.json
	xvfb-run -a sh -c './ops_world --seed 20260928 --fixed --autoclose 0.1 --report /tmp/ops-world-x11.json & pid=$$!; sleep 1; kill -TERM $$pid 2>/dev/null || true; wait $$pid 2>/dev/null || true'

clean:
	rm -f *.o ops_world test_ops_world render_fixtures fixture-*.ppm
