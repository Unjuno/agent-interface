CC ?= cc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Werror -pedantic
LDFLAGS ?= -lm
BIN := build/facility
TESTBIN := build/test_core
SRC := src/main.c src/facility.c

.PHONY: all clean test perf
all: $(BIN) $(TESTBIN)

$(BIN): $(SRC) src/facility.h
	mkdir -p build
	$(CC) $(CFLAGS) -o $@ $(SRC) $(LDFLAGS)

$(TESTBIN): tests/test_core.c src/facility.c src/facility.h
	mkdir -p build
	$(CC) $(CFLAGS) -Isrc -o $@ tests/test_core.c src/facility.c $(LDFLAGS)

clean:
	rm -rf build .test-output

test: $(BIN) $(TESTBIN)
	python3 tests/test_facility.py

perf: $(BIN)
	$(BIN) --bench --seed 424242 --episodes 500 --difficulty 0.6
