"""
memory.py

Simulated main memory for the
Instruction Set and Main Memory Access Simulator.

Every read/write is recorded so that the simulator can:
1. Display memory activity.
2. Count accesses for each addressing mode.
3. Compare the cost of different addressing modes.
"""

from collections import defaultdict


class Memory:

    def __init__(self, size=128):

        self.size = size

        # Main memory cells
        self.cells = [0] * size

        # Complete memory access history
        # Format:
        # (operation, address, value, addressing_mode)
        self.trace = []

        # Number of accesses caused by each mode
        self.access_count_by_mode = defaultdict(int)

        self.read_count = 0
        self.write_count = 0

    # ---------------------------------------------------------
    # READ MEMORY
    # ---------------------------------------------------------

    def read(self, address, mode="?"):

        self._check_bounds(address)

        value = self.cells[address]

        self.trace.append(
            ("READ", address, value, mode)
        )

        self.access_count_by_mode[mode] += 1

        self.read_count += 1

        return value

    # ---------------------------------------------------------
    # WRITE MEMORY
    # ---------------------------------------------------------

    def write(self, address, value, mode="?"):

        self._check_bounds(address)

        self.cells[address] = value

        self.trace.append(
            ("WRITE", address, value, mode)
        )

        self.access_count_by_mode[mode] += 1

        self.write_count += 1

    # ---------------------------------------------------------
    # CHECK VALID ADDRESS
    # ---------------------------------------------------------

    def _check_bounds(self, address):

        if not isinstance(address, int):

            raise TypeError(
                f"Memory address must be an integer: {address}"
            )

        if not 0 <= address < self.size:

            raise IndexError(
                f"Memory address {address} is outside "
                f"the valid range 0-{self.size - 1}."
            )

    # ---------------------------------------------------------
    # MEMORY DUMP
    # ---------------------------------------------------------

    def dump(self, start=0, end=16):

        return self.cells[start:end]

    # ---------------------------------------------------------
    # TOTAL ACCESSES
    # ---------------------------------------------------------

    def total_accesses(self):

        return self.read_count + self.write_count

    # ---------------------------------------------------------
    # PRINT ACCESS SUMMARY
    # ---------------------------------------------------------

    def print_access_summary(self):

        print("\nMemory accesses by addressing mode:")

        print(
            f"{'Mode':<18}"
            f"{'Accesses':>10}"
        )

        print("-" * 28)

        modes = [
            "IMMEDIATE",
            "DIRECT",
            "INDIRECT",
            "REGISTER",
            "REG_INDIRECT",
            "INDEXED"
        ]

        for mode in modes:

            count = self.access_count_by_mode.get(
                mode,
                0
            )

            print(
                f"{mode:<18}"
                f"{count:>10}"
            )

        print("-" * 28)

        print(
            f"{'Reads':<18}"
            f"{self.read_count:>10}"
        )

        print(
            f"{'Writes':<18}"
            f"{self.write_count:>10}"
        )

        print(
            f"{'Total':<18}"
            f"{self.total_accesses():>10}"
        )

    # ---------------------------------------------------------
    # RESET ACCESS STATISTICS
    # ---------------------------------------------------------

    def reset_statistics(self):

        self.trace.clear()

        self.access_count_by_mode.clear()

        self.read_count = 0
        self.write_count = 0