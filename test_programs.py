"""
test_programs.py

Contains:
1. Initial main-memory values.
2. Initial register values.
3. Demo program.
4. Expected test results.
"""

from cpu import (
    Instruction,
    IMMEDIATE,
    DIRECT,
    INDIRECT,
    REGISTER,
    REG_INDIRECT,
    INDEXED
)


# =============================================================
# INITIAL MEMORY
# =============================================================

def initial_memory_setup():

    return {

        # Direct addressing:
        # Memory[10] = 99
        10: 99,

        # Indirect addressing:
        # Memory[20] contains address 30
        20: 30,

        # Actual data
        30: 77,

        # Register indirect:
        # R2 initially contains 40
        40: 88,

        # Indexed:
        # R3 = 50
        # offset = 2
        # EA = 52
        52: 15
    }


# =============================================================
# INITIAL REGISTERS
# =============================================================

def initial_registers():

    return {
        "R0": 0,
        "R1": 5,
        "R2": 40,
        "R3": 50
    }


# =============================================================
# DEMONSTRATION PROGRAM
# =============================================================

def build_demo_program():

    return [

        # Immediate
        # R0 = 7
        Instruction(
            "LOAD",
            IMMEDIATE,
            7,
            dest_reg="R0"
        ),

        # Direct
        # EA = 10
        # R0 = Memory[10] = 99
        Instruction(
            "LOAD",
            DIRECT,
            10,
            dest_reg="R0"
        ),

        # Indirect
        #
        # Memory[20] = 30
        # EA = 30
        # Memory[30] = 77
        Instruction(
            "LOAD",
            INDIRECT,
            20,
            dest_reg="R0"
        ),

        # Register
        #
        # R1 = 5
        # R0 = R1
        Instruction(
            "LOAD",
            REGISTER,
            1,
            dest_reg="R0"
        ),

        # Register Indirect
        #
        # R2 = 40
        # EA = 40
        # Memory[40] = 88
        Instruction(
            "LOAD",
            REG_INDIRECT,
            2,
            dest_reg="R0"
        ),

        # Indexed
        #
        # R3 = 50
        # offset = 2
        #
        # EA = 50 + 2
        # EA = 52
        #
        # Memory[52] = 15
        Instruction(
            "LOAD",
            INDEXED,
            (3, 2),
            dest_reg="R0"
        ),

        # Store the final value
        #
        # Memory[60] = R0
        Instruction(
            "STORE",
            DIRECT,
            60,
            dest_reg="R0"
        ),

        # Stop CPU
        Instruction(
            "HLT",
            IMMEDIATE,
            0
        )
    ]


# =============================================================
# EXPECTED TEST RESULTS
# =============================================================

EXPECTED_RESULTS = [

    # index, mode, expected EA, expected result

    (
        0,
        IMMEDIATE,
        None,
        7
    ),

    (
        1,
        DIRECT,
        10,
        99
    ),

    (
        2,
        INDIRECT,
        30,
        77
    ),

    (
        3,
        REGISTER,
        None,
        5
    ),

    (
        4,
        REG_INDIRECT,
        40,
        88
    ),

    (
        5,
        INDEXED,
        52,
        15
    ),

    (
        6,
        DIRECT,
        60,
        15
    )
]