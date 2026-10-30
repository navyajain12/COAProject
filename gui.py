"""
gui.py

Responsive graphical interface for the
Instruction Set and Main Memory Access Simulator.

Designed for Windows laptops using:
- Maximized window
- Tab-based interface
- Responsive Treeviews
- No dependence on a fixed screen resolution
"""

import tkinter as tk
from tkinter import ttk, messagebox

from memory import Memory

from cpu import (
    CPU,
    ALL_MODES
)

from test_programs import (
    initial_memory_setup,
    initial_registers,
    build_demo_program,
    EXPECTED_RESULTS
)


# =============================================================
# MAIN GUI
# =============================================================

class SimulatorGUI:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Instruction Set and Main Memory Access Simulator"
        )

        # -----------------------------------------------------
        # WINDOWS / LAPTOP RESPONSIVE DISPLAY
        # -----------------------------------------------------

        try:
            # Best option for Windows
            self.root.state("zoomed")

        except tk.TclError:

            # Fallback if zoomed is unavailable
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            width = int(screen_width * 0.92)
            height = int(screen_height * 0.88)

            x = (screen_width - width) // 2
            y = (screen_height - height) // 2

            self.root.geometry(
                f"{width}x{height}+{x}+{y}"
            )

        self.root.minsize(
            1000,
            650
        )

        # -----------------------------------------------------
        # CREATE SIMULATOR
        # -----------------------------------------------------

        self.setup_simulator()

        # -----------------------------------------------------
        # CREATE GUI
        # -----------------------------------------------------

        self.create_gui()

        self.load_program_table()

        self.update_display()


    # =========================================================
    # CREATE / RESET CPU + MEMORY
    # =========================================================

    def setup_simulator(self):

        self.mem = Memory(
            size=128
        )

        # Load initial memory values

        for address, value in initial_memory_setup().items():

            self.mem.cells[address] = value

        # Create CPU

        self.cpu = CPU(
            self.mem
        )

        # Load initial registers

        self.cpu.registers.update(
            initial_registers()
        )

        # Load demonstration program

        self.program = (
            build_demo_program()
        )

        # GUI PC represents the instruction currently displayed
        self.display_pc = 0


    # =========================================================
    # CREATE MAIN GUI
    # =========================================================

    def create_gui(self):

        # -----------------------------------------------------
        # TITLE
        # -----------------------------------------------------

        title_frame = tk.Frame(
            self.root
        )

        title_frame.pack(
            fill="x",
            padx=10,
            pady=(8, 2)
        )

        title = tk.Label(
            title_frame,
            text=(
                "INSTRUCTION SET AND "
                "MAIN MEMORY ACCESS SIMULATOR"
            ),
            font=(
                "Arial",
                19,
                "bold"
            )
        )

        title.pack()

        subtitle = tk.Label(
            title_frame,
            text=(
                "Fetch  •  Decode  •  Effective Address  •  "
                "Execute  •  Main Memory Access Analysis"
            ),
            font=(
                "Arial",
                10
            )
        )

        subtitle.pack(
            pady=(2, 5)
        )

        # -----------------------------------------------------
        # STATUS BAR
        # -----------------------------------------------------

        self.status_label = tk.Label(
            self.root,
            text="STATUS: READY",
            font=(
                "Arial",
                10,
                "bold"
            ),
            relief="groove",
            padx=10,
            pady=5
        )

        self.status_label.pack(
            fill="x",
            padx=15,
            pady=(0, 5)
        )

        # -----------------------------------------------------
        # NOTEBOOK / TABS
        # -----------------------------------------------------

        self.notebook = ttk.Notebook(
            self.root
        )

        self.notebook.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        # Create tabs

        self.execution_tab = tk.Frame(
            self.notebook
        )

        self.memory_tab = tk.Frame(
            self.notebook
        )

        self.comparison_tab = tk.Frame(
            self.notebook
        )

        self.notebook.add(
            self.execution_tab,
            text="  CPU EXECUTION  "
        )

        self.notebook.add(
            self.memory_tab,
            text="  MEMORY ANALYSIS  "
        )

        self.notebook.add(
            self.comparison_tab,
            text="  ACCESS COMPARISON  "
        )

        # Build tabs

        self.create_execution_tab()

        self.create_memory_tab()

        self.create_comparison_tab()


    # =========================================================
    # TAB 1 - CPU EXECUTION
    # =========================================================

    def create_execution_tab(self):

        tab = self.execution_tab

        # Responsive grid

        tab.columnconfigure(
            0,
            weight=1
        )

        tab.columnconfigure(
            1,
            weight=1
        )

        tab.rowconfigure(
            0,
            weight=1
        )

        # =====================================================
        # LEFT COLUMN
        # =====================================================

        left = tk.Frame(
            tab
        )

        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10, 5),
            pady=10
        )

        left.columnconfigure(
            0,
            weight=1
        )

        left.rowconfigure(
            0,
            weight=1
        )

        # -----------------------------------------------------
        # PROGRAM
        # -----------------------------------------------------

        program_frame = tk.LabelFrame(
            left,
            text="Program",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        program_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.program_tree = ttk.Treeview(
            program_frame,
            columns=(
                "PC",
                "Instruction"
            ),
            show="headings",
            height=8
        )

        self.program_tree.heading(
            "PC",
            text="PC"
        )

        self.program_tree.heading(
            "Instruction",
            text="Instruction"
        )

        self.program_tree.column(
            "PC",
            width=60,
            anchor="center",
            stretch=False
        )

        self.program_tree.column(
            "Instruction",
            width=420,
            anchor="w"
        )

        program_scroll = ttk.Scrollbar(
            program_frame,
            orient="vertical",
            command=self.program_tree.yview
        )

        self.program_tree.configure(
            yscrollcommand=program_scroll.set
        )

        self.program_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
            pady=5
        )

        program_scroll.pack(
            side="right",
            fill="y",
            padx=(0, 5),
            pady=5
        )

        # -----------------------------------------------------
        # BUTTONS
        # -----------------------------------------------------

        button_frame = tk.Frame(
            left
        )

        button_frame.grid(
            row=1,
            column=0,
            pady=8
        )

        tk.Button(
            button_frame,
            text="STEP",
            width=11,
            height=2,
            command=self.step_instruction
        ).grid(
            row=0,
            column=0,
            padx=4
        )

        tk.Button(
            button_frame,
            text="RUN ALL",
            width=11,
            height=2,
            command=self.run_all
        ).grid(
            row=0,
            column=1,
            padx=4
        )

        tk.Button(
            button_frame,
            text="RESET",
            width=11,
            height=2,
            command=self.reset
        ).grid(
            row=0,
            column=2,
            padx=4
        )

        tk.Button(
            button_frame,
            text="TEST RESULTS",
            width=13,
            height=2,
            command=self.open_test_results
        ).grid(
            row=0,
            column=3,
            padx=4
        )

        # -----------------------------------------------------
        # CPU STATE
        # -----------------------------------------------------

        cpu_frame = tk.LabelFrame(
            left,
            text="CPU State",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        cpu_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(0, 5)
        )

        self.cpu_label = tk.Label(
            cpu_frame,
            text="",
            font=(
                "Consolas",
                11
            ),
            justify="left",
            anchor="w"
        )

        self.cpu_label.pack(
            fill="x",
            padx=15,
            pady=8
        )

        # =====================================================
        # RIGHT COLUMN
        # =====================================================

        right = tk.Frame(
            tab
        )

        right.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 10),
            pady=10
        )

        right.columnconfigure(
            0,
            weight=1
        )

        right.rowconfigure(
            0,
            weight=1
        )

        right.rowconfigure(
            1,
            weight=1
        )

        right.rowconfigure(
            2,
            weight=1
        )

        # -----------------------------------------------------
        # CURRENT INSTRUCTION
        # -----------------------------------------------------

        current_frame = tk.LabelFrame(
            right,
            text="Current Instruction Analysis",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        current_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            pady=(0, 5)
        )

        self.current_label = tk.Label(
            current_frame,
            text="Press STEP to begin execution.",
            font=(
                "Consolas",
                11
            ),
            justify="left",
            anchor="nw"
        )

        self.current_label.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        # -----------------------------------------------------
        # 16-BIT FORMAT
        # -----------------------------------------------------

        format_frame = tk.LabelFrame(
            right,
            text="16-bit Instruction Format",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        format_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=5
        )

        format_header = tk.Label(
            format_frame,
            text=(
                "4-bit Opcode     |     "
                "3-bit Mode     |     "
                "9-bit Operand"
            ),
            font=(
                "Consolas",
                11,
                "bold"
            )
        )

        format_header.pack(
            pady=(10, 5)
        )

        self.format_label = tk.Label(
            format_frame,
            text="Waiting for instruction...",
            font=(
                "Consolas",
                10
            ),
            justify="left",
            anchor="nw"
        )

        self.format_label.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(5, 10)
        )

        # -----------------------------------------------------
        # EXECUTION TRACE
        # -----------------------------------------------------

        trace_frame = tk.LabelFrame(
            right,
            text="Execution Trace",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        trace_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            pady=(5, 0)
        )

        columns = (
            "PC",
            "Opcode",
            "Mode",
            "EA",
            "Result"
        )

        self.trace_tree = ttk.Treeview(
            trace_frame,
            columns=columns,
            show="headings",
            height=5
        )

        for column in columns:

            self.trace_tree.heading(
                column,
                text=column
            )

            self.trace_tree.column(
                column,
                anchor="center",
                width=100
            )

        self.trace_tree.column(
            "Mode",
            width=140
        )

        trace_scroll = ttk.Scrollbar(
            trace_frame,
            orient="vertical",
            command=self.trace_tree.yview
        )

        self.trace_tree.configure(
            yscrollcommand=trace_scroll.set
        )

        self.trace_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
            pady=5
        )

        trace_scroll.pack(
            side="right",
            fill="y",
            padx=(0, 5),
            pady=5
        )


    # =========================================================
    # TAB 2 - MEMORY ANALYSIS
    # =========================================================

    def create_memory_tab(self):

        tab = self.memory_tab

        tab.columnconfigure(
            0,
            weight=1
        )

        tab.columnconfigure(
            1,
            weight=2
        )

        tab.rowconfigure(
            0,
            weight=1
        )

        # -----------------------------------------------------
        # MAIN MEMORY
        # -----------------------------------------------------

        memory_frame = tk.LabelFrame(
            tab,
            text="Main Memory",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        memory_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(10, 5),
            pady=10
        )

        self.memory_tree = ttk.Treeview(
            memory_frame,
            columns=(
                "Address",
                "Value"
            ),
            show="headings"
        )

        self.memory_tree.heading(
            "Address",
            text="Address"
        )

        self.memory_tree.heading(
            "Value",
            text="Value"
        )

        self.memory_tree.column(
            "Address",
            width=130,
            anchor="center"
        )

        self.memory_tree.column(
            "Value",
            width=130,
            anchor="center"
        )

        memory_scroll = ttk.Scrollbar(
            memory_frame,
            orient="vertical",
            command=self.memory_tree.yview
        )

        self.memory_tree.configure(
            yscrollcommand=memory_scroll.set
        )

        self.memory_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
            pady=5
        )

        memory_scroll.pack(
            side="right",
            fill="y",
            padx=(0, 5),
            pady=5
        )

        # -----------------------------------------------------
        # RIGHT MEMORY SECTION
        # -----------------------------------------------------

        right = tk.Frame(
            tab
        )

        right.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 10),
            pady=10
        )

        right.columnconfigure(
            0,
            weight=1
        )

        right.rowconfigure(
            0,
            weight=1
        )

        right.rowconfigure(
            1,
            weight=2
        )

        # -----------------------------------------------------
        # CURRENT MEMORY OPERATION
        # -----------------------------------------------------

        current_frame = tk.LabelFrame(
            right,
            text="Current Instruction Memory Activity",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        current_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            pady=(0, 5)
        )

        self.bus_tree = ttk.Treeview(
            current_frame,
            columns=(
                "Operation",
                "Address",
                "Value",
                "Mode"
            ),
            show="headings",
            height=5
        )

        headings = {
            "Operation": "Operation",
            "Address": "Address",
            "Value": "Value",
            "Mode": "Addressing Mode"
        }

        for column in (
            "Operation",
            "Address",
            "Value",
            "Mode"
        ):

            self.bus_tree.heading(
                column,
                text=headings[column]
            )

            self.bus_tree.column(
                column,
                width=140,
                anchor="center"
            )

        self.bus_tree.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # -----------------------------------------------------
        # COMPLETE MEMORY TRACE
        # -----------------------------------------------------

        full_trace_frame = tk.LabelFrame(
            right,
            text="Complete Memory Read / Write Trace",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        full_trace_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            pady=(5, 0)
        )

        self.full_trace_tree = ttk.Treeview(
            full_trace_frame,
            columns=(
                "No",
                "Operation",
                "Address",
                "Value",
                "Mode"
            ),
            show="headings"
        )

        headings = {
            "No": "#",
            "Operation": "Operation",
            "Address": "Address",
            "Value": "Value",
            "Mode": "Addressing Mode"
        }

        for column in (
            "No",
            "Operation",
            "Address",
            "Value",
            "Mode"
        ):

            self.full_trace_tree.heading(
                column,
                text=headings[column]
            )

            self.full_trace_tree.column(
                column,
                width=120,
                anchor="center"
            )

        self.full_trace_tree.column(
            "No",
            width=50
        )

        full_scroll = ttk.Scrollbar(
            full_trace_frame,
            orient="vertical",
            command=self.full_trace_tree.yview
        )

        self.full_trace_tree.configure(
            yscrollcommand=full_scroll.set
        )

        self.full_trace_tree.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
            pady=5
        )

        full_scroll.pack(
            side="right",
            fill="y",
            padx=(0, 5),
            pady=5
        )


    # =========================================================
    # TAB 3 - ACCESS COMPARISON
    # =========================================================

    def create_comparison_tab(self):

        tab = self.comparison_tab

        tab.columnconfigure(
            0,
            weight=1
        )

        tab.rowconfigure(
            1,
            weight=1
        )

        # -----------------------------------------------------
        # INTRODUCTION
        # -----------------------------------------------------

        intro = tk.Label(
            tab,
            text=(
                "Comparison of data-memory accesses required "
                "by each addressing mode"
            ),
            font=(
                "Arial",
                12,
                "bold"
            )
        )

        intro.grid(
            row=0,
            column=0,
            pady=(15, 5)
        )

        # -----------------------------------------------------
        # TABLE
        # -----------------------------------------------------

        table_frame = tk.LabelFrame(
            tab,
            text="Addressing Mode Comparison",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        table_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=10
        )

        columns = (
            "Mode",
            "Theoretical",
            "Actual",
            "Explanation"
        )

        self.comparison_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        self.comparison_tree.heading(
            "Mode",
            text="Addressing Mode"
        )

        self.comparison_tree.heading(
            "Theoretical",
            text="Accesses / Operation"
        )

        self.comparison_tree.heading(
            "Actual",
            text="Demo Accesses"
        )

        self.comparison_tree.heading(
            "Explanation",
            text="Explanation"
        )

        self.comparison_tree.column(
            "Mode",
            width=160,
            anchor="center"
        )

        self.comparison_tree.column(
            "Theoretical",
            width=150,
            anchor="center"
        )

        self.comparison_tree.column(
            "Actual",
            width=130,
            anchor="center"
        )

        self.comparison_tree.column(
            "Explanation",
            width=550,
            anchor="w"
        )

        self.comparison_tree.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=5
        )

        # -----------------------------------------------------
        # BOTTOM SUMMARY
        # -----------------------------------------------------

        bottom = tk.Frame(
            tab
        )

        bottom.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 15)
        )

        analysis_frame = tk.LabelFrame(
            bottom,
            text="Analysis",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        analysis_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5)
        )

        analysis_text = (
            "Immediate and Register addressing require no "
            "data-memory access because the operand is already "
            "available in the instruction or CPU register.\n\n"
            "Direct, Register Indirect and Indexed normally "
            "require one data-memory access for the tested "
            "operand operation.\n\n"
            "Indirect addressing requires two reads for the "
            "tested LOAD: one to obtain the effective address "
            "and another to obtain the actual data."
        )

        tk.Label(
            analysis_frame,
            text=analysis_text,
            justify="left",
            wraplength=700,
            font=(
                "Arial",
                10
            )
        ).pack(
            anchor="w",
            padx=15,
            pady=10
        )

        stats_frame = tk.LabelFrame(
            bottom,
            text="Overall Statistics",
            font=(
                "Arial",
                11,
                "bold"
            )
        )

        stats_frame.pack(
            side="right",
            fill="both",
            padx=(5, 0)
        )

        self.total_stats_label = tk.Label(
            stats_frame,
            text="",
            justify="left",
            font=(
                "Consolas",
                10
            )
        )

        self.total_stats_label.pack(
            padx=20,
            pady=10
        )


    # =========================================================
    # LOAD PROGRAM TABLE
    # =========================================================

    def load_program_table(self):

        for item in self.program_tree.get_children():

            self.program_tree.delete(
                item
            )

        for index, instruction in enumerate(
            self.program
        ):

            self.program_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index,
                    str(instruction)
                )
            )


    # =========================================================
    # STEP ONE INSTRUCTION
    # =========================================================

    def step_instruction(self):

        if self.cpu.halted:

            messagebox.showinfo(
                "Execution Complete",
                "The CPU has already halted.\n\n"
                "Press RESET to execute the program again."
            )

            return

        if self.cpu.pc >= len(
            self.program
        ):

            return

        current_pc = self.cpu.pc

        instruction = self.program[
            current_pc
        ]

        self.display_pc = current_pc

        self.status_label.config(
            text=(
                f"STATUS: EXECUTING "
                f"INSTRUCTION {current_pc}"
            )
        )

        # Save current memory trace position

        trace_before = len(
            self.mem.trace
        )

        # -----------------------------------------------------
        # EXECUTE
        # -----------------------------------------------------

        try:

            self.cpu.step(
                instruction
            )

        except Exception as error:

            self.status_label.config(
                text="STATUS: EXECUTION ERROR"
            )

            messagebox.showerror(
                "Execution Error",
                str(error)
            )

            return

        # -----------------------------------------------------
        # GET EXECUTION RESULT
        # -----------------------------------------------------

        (
            executed_instruction,
            effective_address,
            result
        ) = self.cpu.history[-1]

        # -----------------------------------------------------
        # CURRENT INSTRUCTION
        # -----------------------------------------------------

        ea_text = (
            "-"
            if effective_address is None
            else effective_address
        )

        result_text = (
            "-"
            if result is None
            else result
        )

        self.current_label.config(
            text=(
                f"PC                : {current_pc}\n"
                f"Opcode            : {instruction.opcode}\n"
                f"Addressing Mode   : {instruction.mode}\n"
                f"Operand           : {instruction.operand}\n"
                f"Destination       : "
                f"{instruction.dest_reg or '-'}\n"
                f"Effective Address : {ea_text}\n"
                f"Result / Value    : {result_text}"
            )
        )

        # -----------------------------------------------------
        # INSTRUCTION FORMAT
        # -----------------------------------------------------

        self.update_instruction_format(
            instruction
        )

        # -----------------------------------------------------
        # EXECUTION TRACE
        # -----------------------------------------------------

        self.trace_tree.insert(
            "",
            "end",
            values=(
                current_pc,
                instruction.opcode,
                instruction.mode,
                ea_text,
                result_text
            )
        )

        # -----------------------------------------------------
        # CURRENT MEMORY ACTIVITY
        # -----------------------------------------------------

        operations = self.mem.trace[
            trace_before:
        ]

        self.update_current_memory_activity(
            operations
        )

        # -----------------------------------------------------
        # PROGRAM HIGHLIGHT
        # -----------------------------------------------------

        self.highlight_instruction(
            current_pc
        )

        # -----------------------------------------------------
        # UPDATE EVERYTHING
        # -----------------------------------------------------

        self.update_display()

        if self.cpu.halted:

            self.status_label.config(
                text=(
                    "STATUS: PROGRAM HALTED - "
                    "EXECUTION COMPLETE"
                )
            )

        else:

            self.status_label.config(
                text=(
                    f"STATUS: INSTRUCTION "
                    f"{current_pc} COMPLETED"
                )
            )


    # =========================================================
    # RUN ALL
    # =========================================================

    def run_all(self):

        if self.cpu.halted:

            messagebox.showinfo(
                "Execution Complete",
                "The program has already halted.\n\n"
                "Press RESET to run it again."
            )

            return

        self.status_label.config(
            text="STATUS: RUNNING PROGRAM..."
        )

        self.root.update_idletasks()

        safety_counter = 0

        try:

            while (
                not self.cpu.halted
                and
                self.cpu.pc < len(self.program)
            ):

                self.step_instruction()

                safety_counter += 1

                if safety_counter > 1000:

                    self.status_label.config(
                        text="STATUS: EXECUTION STOPPED"
                    )

                    messagebox.showwarning(
                        "Execution Stopped",
                        "Possible infinite loop detected."
                    )

                    return

            self.status_label.config(
                text=(
                    "STATUS: PROGRAM HALTED - "
                    "EXECUTION COMPLETE"
                )
            )

        except Exception as error:

            self.status_label.config(
                text="STATUS: EXECUTION ERROR"
            )

            messagebox.showerror(
                "Execution Error",
                str(error)
            )


    # =========================================================
    # DISPLAY 16-BIT FORMAT
    # =========================================================

    def update_instruction_format(
        self,
        instruction
    ):

        try:

            encoded = instruction.encode()

            binary = format(
                encoded,
                "016b"
            )

            opcode_bits = binary[0:4]
            mode_bits = binary[4:7]
            operand_bits = binary[7:16]

            text = (
                f"Opcode          : {opcode_bits}\n"
                f"Address Mode    : {mode_bits}\n"
                f"Operand         : {operand_bits}\n"
                f"----------------------------------------\n"
                f"16-bit Word     : "
                f"{opcode_bits} {mode_bits} {operand_bits}\n"
                f"Hex Value       : 0x{encoded:04X}"
            )

            if instruction.mode == "INDEXED":

                base_register, offset = (
                    instruction.operand
                )

                text += (
                    "\n\n"
                    f"Indexed Operand : "
                    f"R{base_register} + {offset}"
                )

            self.format_label.config(
                text=text
            )

        except Exception as error:

            self.format_label.config(
                text=(
                    f"Encoding Error: {error}"
                )
            )


    # =========================================================
    # CURRENT MEMORY ACTIVITY
    # =========================================================

    def update_current_memory_activity(
        self,
        operations
    ):

        for item in self.bus_tree.get_children():

            self.bus_tree.delete(
                item
            )

        if not operations:

            self.bus_tree.insert(
                "",
                "end",
                values=(
                    "NONE",
                    "-",
                    "-",
                    "No data-memory access"
                )
            )

            return

        for (
            operation,
            address,
            value,
            mode
        ) in operations:

            self.bus_tree.insert(
                "",
                "end",
                values=(
                    operation,
                    address,
                    value,
                    mode
                )
            )


    # =========================================================
    # HIGHLIGHT CURRENT INSTRUCTION
    # =========================================================

    def highlight_instruction(
        self,
        index
    ):

        item = str(
            index
        )

        if self.program_tree.exists(
            item
        ):

            self.program_tree.selection_set(
                item
            )

            self.program_tree.focus(
                item
            )

            self.program_tree.see(
                item
            )


    # =========================================================
    # UPDATE ALL DISPLAYS
    # =========================================================

    def update_display(self):

        # -----------------------------------------------------
        # CPU
        # -----------------------------------------------------

        ir_text = "-"

        if self.cpu.ir is not None:

            ir_text = str(
                self.cpu.ir
            )

        cpu_text = (
            f"PC = {self.display_pc}\n"
            f"IR = {ir_text}\n\n"
            f"R0 = {self.cpu.registers['R0']}      "
            f"R1 = {self.cpu.registers['R1']}\n"
            f"R2 = {self.cpu.registers['R2']}      "
            f"R3 = {self.cpu.registers['R3']}"
        )

        self.cpu_label.config(
            text=cpu_text
        )

        # -----------------------------------------------------
        # MEMORY
        # -----------------------------------------------------

        for item in self.memory_tree.get_children():

            self.memory_tree.delete(
                item
            )

        for address, value in enumerate(
            self.mem.cells
        ):

            if value != 0:

                self.memory_tree.insert(
                    "",
                    "end",
                    values=(
                        address,
                        value
                    )
                )

        # -----------------------------------------------------
        # COMPLETE MEMORY TRACE
        # -----------------------------------------------------

        for item in self.full_trace_tree.get_children():

            self.full_trace_tree.delete(
                item
            )

        for index, operation in enumerate(
            self.mem.trace,
            start=1
        ):

            (
                operation_type,
                address,
                value,
                mode
            ) = operation

            self.full_trace_tree.insert(
                "",
                "end",
                values=(
                    index,
                    operation_type,
                    address,
                    value,
                    mode
                )
            )

        # -----------------------------------------------------
        # ACCESS COMPARISON
        # -----------------------------------------------------

        for item in self.comparison_tree.get_children():

            self.comparison_tree.delete(
                item
            )

        comparison_data = [

            (
                "IMMEDIATE",
                0,
                "Operand is contained inside the instruction."
            ),

            (
                "DIRECT",
                1,
                "Operand field directly specifies a memory address."
            ),

            (
                "INDIRECT",
                2,
                "Memory is first read for the effective address, "
                "then again for the operand."
            ),

            (
                "REGISTER",
                0,
                "Operand is already stored in a CPU register."
            ),

            (
                "REG_INDIRECT",
                1,
                "Register supplies the effective memory address."
            ),

            (
                "INDEXED",
                1,
                "Effective address = base register + offset."
            )
        ]

        for (
            mode,
            theoretical,
            explanation
        ) in comparison_data:

            actual = (
                self.mem
                .access_count_by_mode
                .get(
                    mode,
                    0
                )
            )

            self.comparison_tree.insert(
                "",
                "end",
                values=(
                    mode,
                    theoretical,
                    actual,
                    explanation
                )
            )

        # -----------------------------------------------------
        # OVERALL STATISTICS
        # -----------------------------------------------------

        data_accesses = (
            self.mem.total_accesses()
        )

        instruction_fetches = (
            self.cpu.instruction_fetches
        )

        total = (
            data_accesses
            + instruction_fetches
        )

        self.total_stats_label.config(
            text=(
                f"Instruction Fetches : "
                f"{instruction_fetches}\n"
                f"Data Reads          : "
                f"{self.mem.read_count}\n"
                f"Data Writes         : "
                f"{self.mem.write_count}\n"
                f"Data Accesses       : "
                f"{data_accesses}\n"
                f"Total Memory Access : "
                f"{total}"
            )
        )


    # =========================================================
    # AUTOMATIC TEST RESULTS
    # =========================================================

    def open_test_results(self):

        if not self.cpu.halted:

            messagebox.showinfo(
                "Run Program First",
                "Please execute the complete program using "
                "RUN ALL before viewing the test results."
            )

            return

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Automatic Test Results"
        )

        # Also maximize this window where possible

        try:
            window.state("zoomed")
        except tk.TclError:
            window.geometry("1000x600")

        title = tk.Label(
            window,
            text="AUTOMATIC TEST RESULTS",
            font=(
                "Arial",
                18,
                "bold"
            )
        )

        title.pack(
            pady=15
        )

        columns = (
            "Test",
            "Mode",
            "ExpectedEA",
            "ObtainedEA",
            "ExpectedValue",
            "ObtainedValue",
            "Result"
        )

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings",
            height=12
        )

        headings = {
            "Test": "Test",
            "Mode": "Addressing Mode",
            "ExpectedEA": "Expected EA",
            "ObtainedEA": "Obtained EA",
            "ExpectedValue": "Expected Value",
            "ObtainedValue": "Obtained Value",
            "Result": "Result"
        }

        for column in columns:

            tree.heading(
                column,
                text=headings[column]
            )

            tree.column(
                column,
                width=130,
                anchor="center"
            )

        tree.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        passed_count = 0

        for (
            index,
            mode,
            expected_ea,
            expected_value
        ) in EXPECTED_RESULTS:

            (
                instruction,
                obtained_ea,
                obtained_value
            ) = self.cpu.history[
                index
            ]

            passed = (
                obtained_ea == expected_ea
                and
                obtained_value == expected_value
            )

            if passed:

                status = "PASS"
                passed_count += 1

            else:

                status = "FAIL"

            tree.insert(
                "",
                "end",
                values=(
                    index + 1,
                    mode,
                    (
                        "-"
                        if expected_ea is None
                        else expected_ea
                    ),
                    (
                        "-"
                        if obtained_ea is None
                        else obtained_ea
                    ),
                    expected_value,
                    obtained_value,
                    status
                )
            )

        tk.Label(
            window,
            text=(
                f"Tests Passed: "
                f"{passed_count} / "
                f"{len(EXPECTED_RESULTS)}"
            ),
            font=(
                "Arial",
                14,
                "bold"
            )
        ).pack(
            pady=10
        )

        tk.Button(
            window,
            text="CLOSE",
            width=15,
            command=window.destroy
        ).pack(
            pady=(0, 15)
        )


    # =========================================================
    # RESET
    # =========================================================

    def reset(self):

        self.setup_simulator()

        # Clear execution trace

        for item in self.trace_tree.get_children():

            self.trace_tree.delete(
                item
            )

        # Clear current memory activity

        for item in self.bus_tree.get_children():

            self.bus_tree.delete(
                item
            )

        # Reset instruction information

        self.current_label.config(
            text="Press STEP to begin execution."
        )

        self.format_label.config(
            text="Waiting for instruction..."
        )

        # Remove selected program instruction

        for item in self.program_tree.selection():

            self.program_tree.selection_remove(
                item
            )

        self.status_label.config(
            text="STATUS: READY"
        )

        # Return to first tab

        self.notebook.select(
            self.execution_tab
        )

        self.update_display()


# =============================================================
# START APPLICATION
# =============================================================

def main():

    root = tk.Tk()

    SimulatorGUI(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()