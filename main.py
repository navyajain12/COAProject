"""
main.py
Runs the demo program, builds an HTML report from the results (report.py),
saves it as output.html, and opens it in your default web browser.
"""

import os
import webbrowser

from memory import Memory
from cpu import CPU
from test_programs import initial_memory_setup, initial_registers, build_demo_program, EXPECTED_RESULTS
from report import generate_html


def main():
    # Keep the clean, pre-run snapshots -- these are what the page's live
    # "Load demo program / Reset" panel starts from, so it always matches
    # the same starting state the static report below is the *result* of.
    starting_cells = initial_memory_setup()
    starting_registers = initial_registers()

    mem = Memory(size=128)
    for addr, value in starting_cells.items():
        mem.cells[addr] = value

    cpu = CPU(mem)
    cpu.registers.update(starting_registers)

    program = build_demo_program()
    cpu.run(program)  # still prints a plain-text trace to the terminal too

    html = generate_html(
        cpu, mem, program, EXPECTED_RESULTS,
        initial_cells=starting_cells,
        initial_registers=starting_registers,
    )
    output_path = os.path.abspath("output.html")
    with open(output_path, "w") as f:
        f.write(html)

    print(f"\nReport written to {output_path} -- opening in your browser...")
    webbrowser.open("file://" + output_path)


if __name__ == "__main__":
    main()
