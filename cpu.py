"""
cpu.py

Mini CPU simulator.

Instruction format:

    4 bits       3 bits          9 bits
+------------+-------------+-------------------+
|   OPCODE   | ADDRESSING  |      OPERAND      |
|            |    MODE     |                   |
+------------+-------------+-------------------+

Total = 16 bits

Supported addressing modes:

IMMEDIATE
DIRECT
INDIRECT
REGISTER
REG_INDIRECT
INDEXED
"""

from memory import Memory


# =============================================================
# ADDRESSING MODES
# =============================================================

IMMEDIATE = "IMMEDIATE"
DIRECT = "DIRECT"
INDIRECT = "INDIRECT"
REGISTER = "REGISTER"
REG_INDIRECT = "REG_INDIRECT"
INDEXED = "INDEXED"


ALL_MODES = [
    IMMEDIATE,
    DIRECT,
    INDIRECT,
    REGISTER,
    REG_INDIRECT,
    INDEXED
]


# =============================================================
# INSTRUCTION CLASS
# =============================================================

class Instruction:

    OPCODES = [
        "LOAD",
        "STORE",
        "ADD",
        "SUB",
        "JMP",
        "HLT"
    ]

    def __init__(
        self,
        opcode,
        mode,
        operand,
        dest_reg=None
    ):

        self.opcode = opcode.upper()
        self.mode = mode
        self.operand = operand
        self.dest_reg = dest_reg

    # ---------------------------------------------------------
    # TEXT REPRESENTATION
    # ---------------------------------------------------------

    def __repr__(self):

        text = (
            f"{self.opcode} "
            f"{self.mode} "
            f"{self.operand}"
        )

        if self.dest_reg is not None:

            text += f" -> {self.dest_reg}"

        return text

    # ---------------------------------------------------------
    # CONVERT OPERAND INTO 9-BIT FIELD
    # ---------------------------------------------------------

    def get_operand_bits(self):

        # Normal integer operand
        if isinstance(self.operand, int):

            return self.operand & 0x1FF

        # Indexed mode:
        #
        # Operand is stored as:
        #
        # (register_number, offset)
        #
        # 2 bits register + 7 bits offset
        #
        # Example:
        # (3,2)
        #
        # register = 11
        # offset   = 0000010
        #
        # operand = 110000010

        if (
            self.mode == INDEXED
            and isinstance(self.operand, tuple)
        ):

            register_number, offset = self.operand

            register_bits = register_number & 0x3
            offset_bits = offset & 0x7F

            return (
                (register_bits << 7)
                | offset_bits
            )

        return 0

    # ---------------------------------------------------------
    # ENCODE 16-BIT INSTRUCTION
    # ---------------------------------------------------------

    def encode(self):

        if self.opcode not in self.OPCODES:

            raise ValueError(
                f"Unknown opcode: {self.opcode}"
            )

        if self.mode not in ALL_MODES:

            raise ValueError(
                f"Unknown addressing mode: {self.mode}"
            )

        opcode_bits = (
            self.OPCODES.index(self.opcode)
            & 0xF
        )

        mode_bits = (
            ALL_MODES.index(self.mode)
            & 0x7
        )

        operand_bits = self.get_operand_bits()

        instruction_word = (
            (opcode_bits << 12)
            | (mode_bits << 9)
            | operand_bits
        )

        return instruction_word

    # ---------------------------------------------------------
    # GET BINARY REPRESENTATION
    # ---------------------------------------------------------

    def binary_string(self):

        encoded = self.encode()

        binary = format(
            encoded,
            "016b"
        )

        return (
            binary[0:4]
            + " "
            + binary[4:7]
            + " "
            + binary[7:16]
        )

    # ---------------------------------------------------------
    # DECODE 16-BIT WORD
    # ---------------------------------------------------------

    @classmethod
    def decode(
        cls,
        word,
        dest_reg=None
    ):

        opcode_number = (
            word >> 12
        ) & 0xF

        mode_number = (
            word >> 9
        ) & 0x7

        operand = word & 0x1FF

        if opcode_number >= len(cls.OPCODES):

            raise ValueError(
                "Invalid opcode in instruction word."
            )

        if mode_number >= len(ALL_MODES):

            raise ValueError(
                "Invalid addressing mode."
            )

        opcode = cls.OPCODES[
            opcode_number
        ]

        mode = ALL_MODES[
            mode_number
        ]

        # Decode indexed operand
        if mode == INDEXED:

            register_number = (
                operand >> 7
            ) & 0x3

            offset = operand & 0x7F

            operand = (
                register_number,
                offset
            )

        return cls(
            opcode,
            mode,
            operand,
            dest_reg
        )


# =============================================================
# CPU CLASS
# =============================================================

class CPU:

    def __init__(
        self,
        memory: Memory,
        num_registers=4
    ):

        self.mem = memory

        self.registers = {
            f"R{i}": 0
            for i in range(num_registers)
        }

        # Program Counter
        self.pc = 0

        # Instruction Register
        self.ir = None

        self.halted = False

        # History:
        #
        # (
        #   instruction,
        #   effective_address,
        #   result
        # )

        self.history = []

        # Number of instruction fetches
        self.instruction_fetches = 0

    # =========================================================
    # EFFECTIVE ADDRESS / OPERAND RESOLUTION
    # =========================================================

    def effective_address(
        self,
        instr: Instruction
    ):

        mode = instr.mode
        operand = instr.operand

        # -----------------------------------------------------
        # IMMEDIATE
        # -----------------------------------------------------

        if mode == IMMEDIATE:

            return None, operand

        # -----------------------------------------------------
        # DIRECT
        # -----------------------------------------------------

        if mode == DIRECT:

            address = operand

            value = self.mem.read(
                address,
                DIRECT
            )

            return address, value

        # -----------------------------------------------------
        # INDIRECT
        # -----------------------------------------------------

        if mode == INDIRECT:

            pointer_address = operand

            real_address = self.mem.read(
                pointer_address,
                INDIRECT
            )

            value = self.mem.read(
                real_address,
                INDIRECT
            )

            return real_address, value

        # -----------------------------------------------------
        # REGISTER
        # -----------------------------------------------------

        if mode == REGISTER:

            register = f"R{operand}"

            value = self.registers[
                register
            ]

            return None, value

        # -----------------------------------------------------
        # REGISTER INDIRECT
        # -----------------------------------------------------

        if mode == REG_INDIRECT:

            register = f"R{operand}"

            address = self.registers[
                register
            ]

            value = self.mem.read(
                address,
                REG_INDIRECT
            )

            return address, value

        # -----------------------------------------------------
        # INDEXED
        # -----------------------------------------------------

        if mode == INDEXED:

            base_register, offset = operand

            register_name = (
                f"R{base_register}"
            )

            address = (
                self.registers[
                    register_name
                ]
                + offset
            )

            value = self.mem.read(
                address,
                INDEXED
            )

            return address, value

        raise ValueError(
            f"Unknown addressing mode: {mode}"
        )

    # =========================================================
    # STORE ADDRESS RESOLUTION
    # =========================================================

    def store_effective(
        self,
        instr: Instruction,
        value
    ):

        mode = instr.mode
        operand = instr.operand

        # -----------------------------------------------------
        # DIRECT
        # -----------------------------------------------------

        if mode == DIRECT:

            address = operand

            self.mem.write(
                address,
                value,
                DIRECT
            )

            return address

        # -----------------------------------------------------
        # INDIRECT
        # -----------------------------------------------------

        if mode == INDIRECT:

            real_address = self.mem.read(
                operand,
                INDIRECT
            )

            self.mem.write(
                real_address,
                value,
                INDIRECT
            )

            return real_address

        # -----------------------------------------------------
        # REGISTER
        # -----------------------------------------------------

        if mode == REGISTER:

            register = f"R{operand}"

            self.registers[
                register
            ] = value

            return None

        # -----------------------------------------------------
        # REGISTER INDIRECT
        # -----------------------------------------------------

        if mode == REG_INDIRECT:

            register = f"R{operand}"

            address = self.registers[
                register
            ]

            self.mem.write(
                address,
                value,
                REG_INDIRECT
            )

            return address

        # -----------------------------------------------------
        # INDEXED
        # -----------------------------------------------------

        if mode == INDEXED:

            base_register, offset = operand

            register_name = (
                f"R{base_register}"
            )

            address = (
                self.registers[
                    register_name
                ]
                + offset
            )

            self.mem.write(
                address,
                value,
                INDEXED
            )

            return address

        raise ValueError(
            f"Cannot STORE using mode {mode}"
        )

    # =========================================================
    # EXECUTE ONE INSTRUCTION
    # =========================================================

    def step(
        self,
        instr: Instruction
    ):

        if self.halted:

            return

        # FETCH

        self.ir = instr

        self.instruction_fetches += 1

        opcode = instr.opcode

        address = None
        result = None

        # -----------------------------------------------------
        # LOAD
        # -----------------------------------------------------

        if opcode == "LOAD":

            address, value = (
                self.effective_address(
                    instr
                )
            )

            self.registers[
                instr.dest_reg
            ] = value

            result = value

        # -----------------------------------------------------
        # STORE
        # -----------------------------------------------------

        elif opcode == "STORE":

            value = self.registers[
                instr.dest_reg
            ]

            address = self.store_effective(
                instr,
                value
            )

            result = value

        # -----------------------------------------------------
        # ADD
        # -----------------------------------------------------

        elif opcode == "ADD":

            address, value = (
                self.effective_address(
                    instr
                )
            )

            self.registers[
                instr.dest_reg
            ] += value

            result = self.registers[
                instr.dest_reg
            ]

        # -----------------------------------------------------
        # SUB
        # -----------------------------------------------------

        elif opcode == "SUB":

            address, value = (
                self.effective_address(
                    instr
                )
            )

            self.registers[
                instr.dest_reg
            ] -= value

            result = self.registers[
                instr.dest_reg
            ]

        # -----------------------------------------------------
        # JMP
        # -----------------------------------------------------

        elif opcode == "JMP":

            if instr.mode != DIRECT:

                raise ValueError(
                    "JMP currently supports DIRECT mode only."
                )

            target = instr.operand

            self.pc = target

            result = target

            self.history.append(
                (
                    instr,
                    target,
                    result
                )
            )

            return

        # -----------------------------------------------------
        # HLT
        # -----------------------------------------------------

        elif opcode == "HLT":

            self.halted = True

        # -----------------------------------------------------
        # INVALID OPCODE
        # -----------------------------------------------------

        else:

            raise ValueError(
                f"Unknown opcode: {opcode}"
            )

        # Save trace

        self.history.append(
            (
                instr,
                address,
                result
            )
        )

        # Move to next instruction

        self.pc += 1

    # =========================================================
    # RUN COMPLETE PROGRAM
    # =========================================================

    def run(self, program):

        print("\nEXECUTION TRACE")
        print("=" * 70)

        safety_counter = 0

        while (
            not self.halted
            and self.pc < len(program)
        ):

            current_pc = self.pc

            instruction = program[
                current_pc
            ]

            before_trace = len(
                self.mem.trace
            )

            self.step(
                instruction
            )

            _, address, result = (
                self.history[-1]
            )

            print(
                f"\nPC = {current_pc}"
            )

            print(
                f"Instruction : {instruction}"
            )

            print(
                f"Binary      : "
                f"{instruction.binary_string()}"
            )

            print(
                f"Mode        : "
                f"{instruction.mode}"
            )

            print(
                f"EA          : "
                f"{address}"
            )

            print(
                f"Result      : "
                f"{result}"
            )

            # Print memory operations caused
            # by this instruction

            new_trace = self.mem.trace[
                before_trace:
            ]

            if new_trace:

                print("Memory:")

                for (
                    operation,
                    mem_address,
                    value,
                    mode
                ) in new_trace:

                    print(
                        f"  {operation} "
                        f"M[{mem_address}] "
                        f"value={value}"
                    )

            else:

                print(
                    "Memory      : "
                    "No data-memory access"
                )

            safety_counter += 1

            if safety_counter > 1000:

                raise RuntimeError(
                    "Possible infinite loop."
                )

        print("\n" + "=" * 70)

        print(
            "Final Registers:",
            self.registers
        )