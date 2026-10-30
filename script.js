
"use strict";

/*
=========================================================
 INSTRUCTION SET AND MAIN MEMORY ACCESS SIMULATOR
 Web Version - JavaScript

 Instruction format:
 4-bit opcode | 3-bit addressing mode | 9-bit operand

 Main memory: 128 integer locations
 Registers: R0, R1, R2, R3

 Features:
 - STEP / RUN ALL / RESET
 - Six addressing modes
 - Effective address calculation
 - Instruction encoding and decoding
 - Memory read/write tracing
 - Memory access statistics
 - Automatic test validation
=========================================================
*/


// =========================================================
// 1. CPU ARCHITECTURE CONSTANTS
// =========================================================

const MEMORY_SIZE = 128;

const OPCODES = [
    "LOAD",
    "STORE",
    "ADD",
    "SUB",
    "JMP",
    "HLT"
];

const ADDRESSING_MODES = [
    "IMMEDIATE",
    "DIRECT",
    "INDIRECT",
    "REGISTER",
    "REG_INDIRECT",
    "INDEXED"
];

const MODE_INFORMATION = [
    {
        mode: "IMMEDIATE",
        theoretical: 0,
        explanation: "Operand is contained inside the instruction."
    },
    {
        mode: "DIRECT",
        theoretical: 1,
        explanation: "Operand directly specifies a memory address."
    },
    {
        mode: "INDIRECT",
        theoretical: 2,
        explanation: "First memory read obtains the effective address; second obtains the data."
    },
    {
        mode: "REGISTER",
        theoretical: 0,
        explanation: "Operand is already stored in a CPU register."
    },
    {
        mode: "REG_INDIRECT",
        theoretical: 1,
        explanation: "Register contains the effective memory address."
    },
    {
        mode: "INDEXED",
        theoretical: 1,
        explanation: "Effective address = base register + offset."
    }
];


// =========================================================
// 2. INITIAL MEMORY AND REGISTERS
// =========================================================

const INITIAL_MEMORY = {
    10: 99,
    20: 30,
    30: 77,
    40: 88,
    52: 15
};

const INITIAL_REGISTERS = {
    R0: 0,
    R1: 5,
    R2: 40,
    R3: 50
};


// =========================================================
// 3. DEMONSTRATION PROGRAM
// =========================================================

const DEMO_PROGRAM = [
    {
        opcode: "LOAD",
        mode: "IMMEDIATE",
        operand: 7,
        destReg: "R0"
    },
    {
        opcode: "LOAD",
        mode: "DIRECT",
        operand: 10,
        destReg: "R0"
    },
    {
        opcode: "LOAD",
        mode: "INDIRECT",
        operand: 20,
        destReg: "R0"
    },
    {
        opcode: "LOAD",
        mode: "REGISTER",
        operand: 1,
        destReg: "R0"
    },
    {
        opcode: "LOAD",
        mode: "REG_INDIRECT",
        operand: 2,
        destReg: "R0"
    },
    {
        opcode: "LOAD",
        mode: "INDEXED",
        operand: [3, 2],
        destReg: "R0"
    },
    {
        opcode: "STORE",
        mode: "DIRECT",
        operand: 60,
        destReg: "R0"
    },
    {
        opcode: "HLT",
        mode: "IMMEDIATE",
        operand: 0,
        destReg: null
    }
];


// =========================================================
// 4. EXPECTED TEST RESULTS
// =========================================================

const EXPECTED_RESULTS = [
    { index: 0, mode: "IMMEDIATE", ea: null, value: 7 },
    { index: 1, mode: "DIRECT", ea: 10, value: 99 },
    { index: 2, mode: "INDIRECT", ea: 30, value: 77 },
    { index: 3, mode: "REGISTER", ea: null, value: 5 },
    { index: 4, mode: "REG_INDIRECT", ea: 40, value: 88 },
    { index: 5, mode: "INDEXED", ea: 52, value: 15 },
    { index: 6, mode: "DIRECT", ea: 60, value: 15 }
];


// =========================================================
// 5. SIMULATOR STATE
// =========================================================

let memory;
let registers;
let pc;
let ir;
let halted;

let instructionFetches;
let dataReads;
let dataWrites;

let memoryTrace;
let executionHistory;
let currentMemoryOperations;
let accessCountByMode;

let lastExecutedPC;
let currentInstruction;
let currentResult;
let executionStatus;
let executionMessage;
let executionError;


// =========================================================
// 6. INITIALIZE / RESET SIMULATOR
// =========================================================

function initializeSimulator() {

    memory = Array(MEMORY_SIZE).fill(0);

    for (const [address, value] of Object.entries(INITIAL_MEMORY)) {
        memory[Number(address)] = value;
    }

    registers = { ...INITIAL_REGISTERS };

    pc = 0;
    ir = null;
    halted = false;

    instructionFetches = 0;
    dataReads = 0;
    dataWrites = 0;

    memoryTrace = [];
    executionHistory = [];
    currentMemoryOperations = [];

    accessCountByMode = {};

    for (const mode of ADDRESSING_MODES) {
        accessCountByMode[mode] = 0;
    }

    lastExecutedPC = null;
    currentInstruction = null;
    currentResult = null;

    executionStatus = "READY";
    executionMessage = "Press STEP to begin execution.";
    executionError = null;

    renderAll();
}


// =========================================================
// 7. MEMORY ADDRESS VALIDATION
// =========================================================

function checkMemoryAddress(address) {

    if (
        !Number.isInteger(address) ||
        address < 0 ||
        address >= MEMORY_SIZE
    ) {
        throw new Error(
            `Invalid memory address: ${address}. ` +
            `Valid range is 0-${MEMORY_SIZE - 1}.`
        );
    }
}


// =========================================================
// 8. MEMORY READ
// =========================================================

function readMemory(address, mode) {

    checkMemoryAddress(address);

    const value = memory[address];

    const operation = {
        type: "READ",
        address,
        value,
        mode
    };

    memoryTrace.push(operation);
    currentMemoryOperations.push(operation);

    dataReads++;

    accessCountByMode[mode]++;

    return value;
}


// =========================================================
// 9. MEMORY WRITE
// =========================================================

function writeMemory(address, value, mode) {

    checkMemoryAddress(address);

    memory[address] = value;

    const operation = {
        type: "WRITE",
        address,
        value,
        mode
    };

    memoryTrace.push(operation);
    currentMemoryOperations.push(operation);

    dataWrites++;

    accessCountByMode[mode]++;
}


// =========================================================
// 10. REGISTER VALIDATION
// =========================================================

function getRegisterName(number) {

    if (
        !Number.isInteger(number) ||
        number < 0 ||
        number > 3
    ) {
        throw new Error(
            `Invalid register number: ${number}`
        );
    }

    return `R${number}`;
}


// =========================================================
// 11. RESOLVE EFFECTIVE ADDRESS AND OPERAND
// =========================================================

function resolveOperand(instruction) {

    const mode = instruction.mode;
    const operand = instruction.operand;

    switch (mode) {

        // ---------------------------------------------
        // IMMEDIATE
        // ---------------------------------------------

        case "IMMEDIATE":

            return {
                ea: null,
                value: operand
            };


        // ---------------------------------------------
        // DIRECT
        // ---------------------------------------------

        case "DIRECT":

            return {
                ea: operand,
                value: readMemory(operand, mode)
            };


        // ---------------------------------------------
        // INDIRECT
        // ---------------------------------------------

        case "INDIRECT": {

            // First read obtains the real address.
            const realAddress = readMemory(operand, mode);

            // Second read obtains the actual data.
            const value = readMemory(realAddress, mode);

            return {
                ea: realAddress,
                value
            };
        }


        // ---------------------------------------------
        // REGISTER
        // ---------------------------------------------

        case "REGISTER": {

            const registerName = getRegisterName(operand);

            return {
                ea: null,
                value: registers[registerName]
            };
        }


        // ---------------------------------------------
        // REGISTER INDIRECT
        // ---------------------------------------------

        case "REG_INDIRECT": {

            const registerName = getRegisterName(operand);
            const address = registers[registerName];

            return {
                ea: address,
                value: readMemory(address, mode)
            };
        }


        // ---------------------------------------------
        // INDEXED
        // ---------------------------------------------

        case "INDEXED": {

            const [baseRegister, offset] = operand;

            const registerName = getRegisterName(baseRegister);

            const address = registers[registerName] + offset;

            return {
                ea: address,
                value: readMemory(address, mode)
            };
        }


        default:

            throw new Error(
                `Unknown addressing mode: ${mode}`
            );
    }
}


// =========================================================
// 12. RESOLVE STORE ADDRESS
// =========================================================

function resolveStoreAddress(instruction) {

    const mode = instruction.mode;
    const operand = instruction.operand;

    switch (mode) {

        case "DIRECT":
            return operand;

        case "INDIRECT":
            return readMemory(operand, mode);

        case "REG_INDIRECT": {

            const registerName = getRegisterName(operand);
            return registers[registerName];
        }

        case "INDEXED": {

            const [baseRegister, offset] = operand;
            const registerName = getRegisterName(baseRegister);

            return registers[registerName] + offset;
        }

        default:

            throw new Error(
                `STORE does not support ${mode} addressing in this operation.`
            );
    }
}


// =========================================================
// 13. INSTRUCTION ENCODING
// =========================================================

function encodeInstruction(instruction) {

    const opcodeNumber = OPCODES.indexOf(instruction.opcode);
    const modeNumber = ADDRESSING_MODES.indexOf(instruction.mode);

    if (opcodeNumber === -1) {
        throw new Error(`Invalid opcode: ${instruction.opcode}`);
    }

    if (modeNumber === -1) {
        throw new Error(`Invalid mode: ${instruction.mode}`);
    }

    let operandBits;

    if (instruction.mode === "INDEXED") {

        const [registerNumber, offset] = instruction.operand;

        // Indexed format:
        // 2 bits register + 7 bits offset.

        if (
            !Number.isInteger(registerNumber) ||
            registerNumber < 0 ||
            registerNumber > 3 ||
            !Number.isInteger(offset) ||
            offset < 0 ||
            offset > 127
        ) {
            throw new Error("Invalid indexed operand.");
        }

        operandBits = (registerNumber << 7) | offset;

    } else {

        if (
            !Number.isInteger(instruction.operand) ||
            instruction.operand < 0 ||
            instruction.operand > 511
        ) {
            throw new Error(
                "Operand must fit inside 9 bits (0-511)."
            );
        }

        operandBits = instruction.operand;
    }

    const word =
        (opcodeNumber << 12) |
        (modeNumber << 9) |
        operandBits;

    const binary = word.toString(2).padStart(16, "0");

    return {
        word,
        opcodeBits: binary.slice(0, 4),
        modeBits: binary.slice(4, 7),
        operandBits: binary.slice(7, 16),
        binary,
        formattedBinary:
            `${binary.slice(0, 4)} ` +
            `${binary.slice(4, 7)} ` +
            `${binary.slice(7, 16)}`,
        hex: "0x" + word.toString(16).toUpperCase().padStart(4, "0")
    };
}


// =========================================================
// 14. INSTRUCTION DECODING
// =========================================================

function decodeInstruction(word) {

    if (
        !Number.isInteger(word) ||
        word < 0 ||
        word > 65535
    ) {
        throw new Error("Invalid 16-bit instruction word.");
    }

    const opcodeNumber = (word >> 12) & 0xF;
    const modeNumber = (word >> 9) & 0x7;
    const rawOperand = word & 0x1FF;

    if (
        opcodeNumber >= OPCODES.length ||
        modeNumber >= ADDRESSING_MODES.length
    ) {
        throw new Error("Instruction contains an invalid field.");
    }

    const mode = ADDRESSING_MODES[modeNumber];

    let operand = rawOperand;

    if (mode === "INDEXED") {
        operand = [
            (rawOperand >> 7) & 0x3,
            rawOperand & 0x7F
        ];
    }

    return {
        opcode: OPCODES[opcodeNumber],
        mode,
        operand
    };
}


// =========================================================
// 15. DISPLAY INSTRUCTION AS TEXT
// =========================================================

function instructionToString(instruction) {

    if (instruction.opcode === "HLT") {
        return "HLT";
    }

    let operandText;

    if (instruction.mode === "INDEXED") {
        const [registerNumber, offset] = instruction.operand;
        operandText = `R${registerNumber} + ${offset}`;
    } else if (instruction.mode === "REGISTER") {
        operandText = `R${instruction.operand}`;
    } else if (instruction.mode === "REG_INDIRECT") {
        operandText = `(R${instruction.operand})`;
    } else {
        operandText = String(instruction.operand);
    }

    const destination = instruction.destReg
        ? ` -> ${instruction.destReg}`
        : "";

    return (
        `${instruction.opcode} ` +
        `${instruction.mode} ` +
        `${operandText}${destination}`
    );
}


// =========================================================
// 16. EXECUTE ONE INSTRUCTION
// =========================================================

function stepInstruction() {

    if (halted) {
        return false;
    }

    if (pc >= DEMO_PROGRAM.length) {
        halted = true;
        executionStatus = "HALTED";
        executionMessage = "End of program reached.";
        renderAll();
        return false;
    }

    const currentPC = pc;
    const instruction = DEMO_PROGRAM[currentPC];

    try {

        // Validate encoding before execution.
        const encoding = encodeInstruction(instruction);

        // Verify the encoded fields can be decoded.
        const decoded = decodeInstruction(encoding.word);

        if (
            decoded.opcode !== instruction.opcode ||
            decoded.mode !== instruction.mode ||
            JSON.stringify(decoded.operand) !==
            JSON.stringify(instruction.operand)
        ) {
            throw new Error("Instruction encoding/decoding mismatch.");
        }

        currentMemoryOperations = [];

        ir = instruction;
        currentInstruction = instruction;
        lastExecutedPC = currentPC;

        instructionFetches++;

        let effectiveAddress = null;
        let result = null;
        let nextPC = currentPC + 1;

        switch (instruction.opcode) {

            // -----------------------------------------
            // LOAD
            // -----------------------------------------

            case "LOAD": {

                const resolved = resolveOperand(instruction);

                effectiveAddress = resolved.ea;
                result = resolved.value;

                registers[instruction.destReg] = result;

                break;
            }


            // -----------------------------------------
            // STORE
            // -----------------------------------------

            case "STORE": {

                result = registers[instruction.destReg];

                if (instruction.mode === "REGISTER") {

                    const registerName =
                        getRegisterName(instruction.operand);

                    registers[registerName] = result;

                } else {

                    effectiveAddress =
                        resolveStoreAddress(instruction);

                    writeMemory(
                        effectiveAddress,
                        result,
                        instruction.mode
                    );
                }

                break;
            }


            // -----------------------------------------
            // ADD
            // -----------------------------------------

            case "ADD": {

                const resolved = resolveOperand(instruction);

                effectiveAddress = resolved.ea;

                registers[instruction.destReg] += resolved.value;

                result = registers[instruction.destReg];

                break;
            }


            // -----------------------------------------
            // SUB
            // -----------------------------------------

            case "SUB": {

                const resolved = resolveOperand(instruction);

                effectiveAddress = resolved.ea;

                registers[instruction.destReg] -= resolved.value;

                result = registers[instruction.destReg];

                break;
            }


            // -----------------------------------------
            // JMP
            // -----------------------------------------

            case "JMP": {

                if (instruction.mode !== "DIRECT") {
                    throw new Error("JMP supports DIRECT mode only.");
                }

                const target = instruction.operand;

                if (
                    !Number.isInteger(target) ||
                    target < 0 ||
                    target >= DEMO_PROGRAM.length
                ) {
                    throw new Error(`Invalid jump target: ${target}`);
                }

                effectiveAddress = target;
                result = target;
                nextPC = target;

                break;
            }


            // -----------------------------------------
            // HALT
            // -----------------------------------------

            case "HLT": {

                halted = true;
                break;
            }


            default:

                throw new Error(
                    `Unknown opcode: ${instruction.opcode}`
                );
        }

        pc = nextPC;

        const historyEntry = {
            pc: currentPC,
            instruction,
            ea: effectiveAddress,
            result,
            encoding,
            memoryOperations: [...currentMemoryOperations]
        };

        executionHistory.push(historyEntry);
        currentResult = historyEntry;

        if (halted) {

            executionStatus = "HALTED";
            executionMessage =
                "Program execution completed successfully.";

        } else {

            executionStatus = "READY";
            executionMessage =
                `Instruction ${currentPC} executed successfully.`;
        }

        renderAll();

        return true;

    } catch (error) {

        halted = true;
        executionError = error.message;

        executionStatus = "ERROR";
        executionMessage = error.message;

        renderAll();

        return false;
    }
}


// =========================================================
// 17. RUN COMPLETE PROGRAM
// =========================================================

function runAll() {

    if (halted) {
        return;
    }

    let safetyCounter = 0;
    const MAX_STEPS = 1000;

    while (!halted && pc < DEMO_PROGRAM.length) {

        const success = stepInstruction();

        if (!success) {
            break;
        }

        safetyCounter++;

        if (safetyCounter >= MAX_STEPS && !halted) {

            halted = true;
            executionStatus = "ERROR";
            executionMessage =
                "Execution stopped: possible infinite loop.";

            renderAll();
            break;
        }
    }

    if (!halted && pc >= DEMO_PROGRAM.length) {

        halted = true;
        executionStatus = "HALTED";
        executionMessage = "End of program reached.";

        renderAll();
    }
}


// =========================================================
// 18. RESET PROGRAM
// =========================================================

function resetSimulator() {

    initializeSimulator();

    activateTab("execution");
}


// =========================================================
// 19. DOM HELPER FUNCTIONS
// =========================================================

function getElement(id) {
    return document.getElementById(id);
}

function setText(id, value) {

    const element = getElement(id);

    if (element) {
        element.textContent = String(value);
    }
}

function displayValue(value) {

    return value === null || value === undefined
        ? "-"
        : String(value);
}

function clearTable(id) {

    const body = getElement(id);

    if (body) {
        body.replaceChildren();
    }
}

function addTableRow(bodyId, values, className = "") {

    const body = getElement(bodyId);

    if (!body) {
        return null;
    }

    const row = document.createElement("tr");

    if (className) {
        row.className = className;
    }

    for (const value of values) {

        const cell = document.createElement("td");
        cell.textContent = displayValue(value);

        row.appendChild(cell);
    }

    body.appendChild(row);

    return row;
}


// =========================================================
// 20. RENDER STATUS
// =========================================================

function renderStatus() {

    const statusElement = getElement("cpuStatus");

    if (!statusElement) {
        return;
    }

    statusElement.textContent = executionStatus;

    statusElement.className = "";

    switch (executionStatus) {

        case "HALTED":
            statusElement.classList.add("status-halted");
            break;

        case "ERROR":
            statusElement.classList.add("status-error");
            break;

        case "RUNNING":
            statusElement.classList.add("status-running");
            break;

        default:
            statusElement.classList.add("status-ready");
    }

    setText("executionMessage", executionMessage);

    const stepButton = getElement("stepBtn");
    const runButton = getElement("runBtn");

    if (stepButton) {
        stepButton.disabled = halted;
    }

    if (runButton) {
        runButton.disabled = halted;
    }
}


// =========================================================
// 21. RENDER PROGRAM
// =========================================================

function renderProgram() {

    clearTable("programBody");

    DEMO_PROGRAM.forEach((instruction, index) => {

        const rowClass =
            index === lastExecutedPC
                ? "current-instruction"
                : "";

        addTableRow(
            "programBody",
            [
                index,
                instructionToString(instruction)
            ],
            rowClass
        );
    });
}


// =========================================================
// 22. RENDER CPU REGISTERS
// =========================================================

function renderCPU() {

    setText(
        "currentPC",
        lastExecutedPC === null ? "-" : lastExecutedPC
    );

    setText("nextPC", pc);

    setText(
        "instructionRegister",
        ir ? instructionToString(ir) : "-"
    );

    for (const registerName of Object.keys(registers)) {

        setText(
            `reg${registerName}`,
            registers[registerName]
        );
    }
}


// =========================================================
// 23. RENDER CURRENT INSTRUCTION
// =========================================================

function renderCurrentInstruction() {

    if (!currentResult) {

        setText("currentOpcode", "-");
        setText("currentMode", "-");
        setText("currentOperand", "-");
        setText("currentDestination", "-");
        setText("effectiveAddress", "-");
        setText("instructionResult", "-");

        return;
    }

    const instruction = currentResult.instruction;

    setText("currentOpcode", instruction.opcode);
    setText("currentMode", instruction.mode);

    let operandText;

    if (instruction.mode === "INDEXED") {

        const [baseRegister, offset] = instruction.operand;

        operandText = `R${baseRegister} + ${offset}`;

    } else {

        operandText = instruction.operand;
    }

    setText("currentOperand", operandText);

    setText(
        "currentDestination",
        instruction.destReg || "-"
    );

    setText(
        "effectiveAddress",
        displayValue(currentResult.ea)
    );

    setText(
        "instructionResult",
        displayValue(currentResult.result)
    );
}


// =========================================================
// 24. RENDER 16-BIT ENCODING
// =========================================================

function renderInstructionEncoding() {

    if (!currentResult) {

        setText("opcodeBits", "0000");
        setText("modeBits", "000");
        setText("operandBits", "000000000");

        setText(
            "binaryInstruction",
            "0000 000 000000000"
        );

        setText("hexInstruction", "0x0000");

        setText(
            "encodingNote",
            "The destination register is stored separately " +
            "in this simplified instruction model."
        );

        return;
    }

    const encoding = currentResult.encoding;
    const instruction = currentResult.instruction;

    setText("opcodeBits", encoding.opcodeBits);
    setText("modeBits", encoding.modeBits);
    setText("operandBits", encoding.operandBits);

    setText(
        "binaryInstruction",
        encoding.formattedBinary
    );

    setText("hexInstruction", encoding.hex);

    if (instruction.mode === "INDEXED") {

        const [registerNumber, offset] = instruction.operand;

        setText(
            "encodingNote",
            `Indexed operand: R${registerNumber} + ${offset}. ` +
            "The 9-bit operand field contains a 2-bit " +
            "register number and a 7-bit offset. " +
            "The destination register is separate."
        );

    } else {

        setText(
            "encodingNote",
            "The destination register is stored separately " +
            "in this simplified instruction model."
        );
    }
}


// =========================================================
// 25. RENDER EXECUTION TRACE
// =========================================================

function renderExecutionTrace() {

    clearTable("executionBody");

    executionHistory.forEach(entry => {

        addTableRow(
            "executionBody",
            [
                entry.pc,
                entry.instruction.opcode,
                entry.instruction.mode,
                entry.ea,
                entry.result
            ]
        );
    });
}


// =========================================================
// 26. RENDER MAIN MEMORY
// =========================================================

function renderMemory() {

    clearTable("memoryBody");

    // Show non-zero locations, matching the Python GUI.
    memory.forEach((value, address) => {

        if (value !== 0) {

            addTableRow(
                "memoryBody",
                [address, value]
            );
        }
    });
}


// =========================================================
// 27. RENDER CURRENT MEMORY OPERATIONS
// =========================================================

function renderCurrentMemoryActivity() {

    clearTable("currentMemoryBody");

    if (currentMemoryOperations.length === 0) {

        addTableRow(
            "currentMemoryBody",
            [
                "NONE",
                "-",
                "-",
                "No data-memory access"
            ]
        );

        return;
    }

    currentMemoryOperations.forEach(operation => {

        addTableRow(
            "currentMemoryBody",
            [
                operation.type,
                operation.address,
                operation.value,
                operation.mode
            ]
        );
    });
}


// =========================================================
// 28. RENDER COMPLETE MEMORY TRACE
// =========================================================

function renderFullMemoryTrace() {

    clearTable("fullMemoryBody");

    memoryTrace.forEach((operation, index) => {

        addTableRow(
            "fullMemoryBody",
            [
                index + 1,
                operation.type,
                operation.address,
                operation.value,
                operation.mode
            ]
        );
    });
}


// =========================================================
// 29. RENDER ACCESS COMPARISON
// =========================================================

function renderComparison() {

    clearTable("comparisonBody");

    MODE_INFORMATION.forEach(info => {

        addTableRow(
            "comparisonBody",
            [
                info.mode,
                info.theoretical,
                accessCountByMode[info.mode],
                info.explanation
            ]
        );
    });
}


// =========================================================
// 30. RENDER STATISTICS
// =========================================================

function renderStatistics() {

    const totalDataAccesses = dataReads + dataWrites;

    const totalMemoryAccesses =
        instructionFetches + totalDataAccesses;

    setText("instructionFetches", instructionFetches);
    setText("dataReads", dataReads);
    setText("dataWrites", dataWrites);
    setText("totalDataAccesses", totalDataAccesses);
    setText("totalMemoryAccesses", totalMemoryAccesses);
}


// =========================================================
// 31. RENDER TEST RESULTS
// =========================================================

function renderTestResults() {

    clearTable("testResultsBody");

    let passedCount = 0;

    EXPECTED_RESULTS.forEach(test => {

        const entry = executionHistory.find(
            item => item.pc === test.index
        );

        // The test is pending until its instruction runs.
        if (!entry) {

            addTableRow(
                "testResultsBody",
                [
                    test.index + 1,
                    test.mode,
                    test.ea,
                    "-",
                    test.value,
                    "-",
                    "PENDING"
                ]
            );

            return;
        }

        const passed =
            entry.ea === test.ea &&
            entry.result === test.value &&
            entry.instruction.mode === test.mode;

        if (passed) {
            passedCount++;
        }

        addTableRow(
            "testResultsBody",
            [
                test.index + 1,
                test.mode,
                test.ea,
                entry.ea,
                test.value,
                entry.result,
                passed ? "PASS" : "FAIL"
            ],
            passed ? "pass" : "fail"
        );
    });

    setText(
        "testsPassed",
        `${passedCount} / ${EXPECTED_RESULTS.length}`
    );
}


// =========================================================
// 32. RENDER COMPLETE APPLICATION
// =========================================================

function renderAll() {

    renderStatus();
    renderProgram();
    renderCPU();
    renderCurrentInstruction();
    renderInstructionEncoding();
    renderExecutionTrace();

    renderMemory();
    renderCurrentMemoryActivity();
    renderFullMemoryTrace();

    renderComparison();
    renderStatistics();
    renderTestResults();
}


// =========================================================
// 33. TAB NAVIGATION
// =========================================================

function activateTab(tabId) {

    document.querySelectorAll(".tab-button").forEach(button => {

        const isActive = button.dataset.tab === tabId;

        button.classList.toggle("active", isActive);
        button.setAttribute(
            "aria-selected",
            String(isActive)
        );
    });

    document.querySelectorAll(".tab-content").forEach(section => {

        section.classList.toggle(
            "active",
            section.id === tabId
        );
    });
}


// =========================================================
// 34. EVENT LISTENERS
// =========================================================

function setupEventListeners() {

    const stepButton = getElement("stepBtn");
    const runButton = getElement("runBtn");
    const resetButton = getElement("resetBtn");

    if (stepButton) {

        stepButton.addEventListener(
            "click",
            stepInstruction
        );
    }

    if (runButton) {

        runButton.addEventListener(
            "click",
            runAll
        );
    }

    if (resetButton) {

        resetButton.addEventListener(
            "click",
            resetSimulator
        );
    }

    document.querySelectorAll(".tab-button").forEach(button => {

        button.addEventListener("click", () => {

            activateTab(button.dataset.tab);
        });
    });
}


// =========================================================
// 35. APPLICATION STARTUP
// =========================================================

document.addEventListener("DOMContentLoaded", () => {

    setupEventListeners();

    initializeSimulator();

    activateTab("execution");
});
