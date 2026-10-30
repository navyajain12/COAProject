# Instruction Set and Main Memory Access Simulator

A Python-based CPU simulation project developed as part of Computer Organization and Architecture (COA).

## Overview

This project demonstrates how a CPU processes instructions, calculates effective addresses using different addressing modes, and performs main memory read/write operations.

It includes an interactive graphical interface for visualizing instruction execution and analyzing memory access counts.

## Key Features

- Custom 16-bit instruction format
- Six addressing modes: Immediate, Direct, Indirect, Register, Register Indirect, and Indexed
- Step-by-step instruction execution
- CPU register and Program Counter tracking
- Effective address calculation
- Main memory read/write tracing
- Memory access comparison across addressing modes
- Automatic test-case verification
- Interactive GUI with three analysis tabs

## Technologies Used

- Python
- Tkinter
- Computer Organization and Architecture concepts

## Project Structure

```text
main.py          - Application entry point
gui.py           - Graphical user interface
cpu.py           - CPU and instruction execution
memory.py        - Main memory simulation
test_programs.py - Sample program and test cases
```

## How to Run

1. Install Python 3.
2. Download or clone this repository.
3. Open the project folder in VS Code.
4. Run:

```bash
python main.py
```

The simulator will launch in a graphical window.

## Learning Outcomes

This project explores instruction encoding, addressing modes, the Fetch–Decode–Execute cycle, effective address generation, CPU registers, and memory access behavior.
