"""
report.py
Turns the data already produced by CPU.run() / Memory (mem.trace, cpu.history,
mem.access_count_by_mode) into a single self-contained HTML page, so a run of
main.py can be viewed in a browser instead of scrolled through in a terminal.

On top of the static run report, the page also embeds a small, fully live
simulator panel (same addressing-mode logic, re-implemented in JS) so you can:
  - replay the demo program step by step with memory cells highlighting live
  - type in and run any custom instruction on the spot, no terminal needed
This needs no server -- it's one self-contained HTML file, opened locally.
"""

import json

STYLE = """
<style>
body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f6f7fb;color:#1c2130;margin:0;padding:24px;}
.wrap{max-width:960px;margin:0 auto;}
h1{font-size:1.4rem;margin-bottom:4px;}
h2{font-size:1rem;text-transform:uppercase;letter-spacing:.04em;color:#5b6478;margin:28px 0 10px;}
table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #dde1ea;border-radius:10px;overflow:hidden;}
th,td{padding:8px 10px;text-align:left;font-size:0.86rem;border-bottom:1px solid #eef0f5;}
th{background:#eef1fb;color:#333;}
tr:last-child td{border-bottom:none;}
.pass{color:#1f9d55;font-weight:600;}
.fail{color:#e2543a;font-weight:600;}
.regs span{display:inline-block;background:#eef7f6;border:1px solid #0f9d8f;border-radius:8px;
  padding:6px 12px;margin:0 6px 6px 0;font-size:0.85rem;}
.bar-row{display:grid;grid-template-columns:140px 1fr 40px;align-items:center;gap:8px;margin-bottom:6px;font-size:0.85rem;}
.bar-track{background:#eef0f5;border-radius:6px;height:10px;overflow:hidden;}
.bar-fill{background:#e2543a;height:100%;transition:width .25s ease;}

/* ---- interactive panel ---- */
.panel{background:#fff;border:1px solid #dde1ea;border-radius:10px;padding:16px;margin-bottom:18px;}
.panel h3{margin:0 0 10px;font-size:0.95rem;}
.row{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;margin-bottom:10px;}
.field{display:flex;flex-direction:column;font-size:0.78rem;color:#5b6478;gap:3px;}
.field select,.field input{padding:6px 8px;border:1px solid #dde1ea;border-radius:6px;font-size:0.85rem;min-width:90px;}
button{background:#0f9d8f;color:#fff;border:none;border-radius:6px;padding:7px 14px;font-size:0.85rem;cursor:pointer;}
button.secondary{background:#5b6478;}
button.danger{background:#e2543a;}
button:disabled{background:#c6cad4;cursor:not-allowed;}
.btnrow{display:flex;gap:8px;flex-wrap:wrap;}
.err{color:#e2543a;font-size:0.8rem;margin-top:4px;min-height:1em;}
.status{font-size:0.8rem;color:#5b6478;margin-top:4px;}

.mem-grid{display:grid;grid-template-columns:repeat(16,1fr);gap:4px;margin-top:6px;}
.cell{background:#f6f7fb;border:1px solid #e4e7ee;border-radius:5px;padding:3px 2px;text-align:center;font-size:0.68rem;transition:background .15s,border-color .15s,transform .15s;}
.cell .a{color:#9aa1b1;font-size:0.62rem;display:block;}
.cell .v{font-weight:600;}
.cell.touched-read{background:#eaf6ff;border-color:#3b82f6;transform:scale(1.07);}
.cell.touched-write{background:#fff1ec;border-color:#e2543a;transform:scale(1.07);}

.trace-log{max-height:220px;overflow-y:auto;border:1px solid #eef0f5;border-radius:8px;}
.trace-log table{border:none;border-radius:0;}

.legend{font-size:0.75rem;color:#5b6478;margin-top:6px;}
.legend span{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:middle;}
</style>
"""

INTERACTIVE_TEMPLATE = """
<div class="panel">
  <h3>Live simulator</h3>
  <div class="btnrow">
    <button id="btnLoadDemo">Load demo program</button>
    <button id="btnStep" class="secondary" disabled>Step &rarr;</button>
    <button id="btnReset" class="danger">Reset</button>
  </div>
  <div class="status" id="demoStatus">No program loaded yet.</div>

  <h3 style="margin-top:18px;">Run a custom instruction</h3>
  <div class="row">
    <div class="field"><label>Opcode</label>
      <select id="inOpcode">
        <option>LOAD</option><option>STORE</option><option>ADD</option>
        <option>SUB</option><option>HLT</option>
      </select>
    </div>
    <div class="field"><label>Mode</label>
      <select id="inMode">
        <option>IMMEDIATE</option><option>DIRECT</option><option>INDIRECT</option>
        <option>REGISTER</option><option>REG_INDIRECT</option><option>INDEXED</option>
      </select>
    </div>
    <div class="field" id="operandSingleWrap"><label>Operand</label>
      <input id="inOperand" type="number" value="0">
    </div>
    <div class="field" id="operandRegWrap" style="display:none;"><label>Base reg #</label>
      <input id="inBaseReg" type="number" value="0" min="0">
    </div>
    <div class="field" id="operandOffWrap" style="display:none;"><label>Offset</label>
      <input id="inOffset" type="number" value="0">
    </div>
    <div class="field"><label>Dest register</label>
      <select id="inDestReg"></select>
    </div>
    <div class="field"><button id="btnRun">Run instruction</button></div>
  </div>
  <div class="err" id="runError"></div>

  <h3 style="margin-top:18px;">Registers</h3>
  <div class="regs" id="liveRegs"></div>

  <h3>Memory</h3>
  <div class="mem-grid" id="memGrid"></div>
  <div class="legend">
    <span style="background:#3b82f6;"></span> just read &nbsp;&nbsp;
    <span style="background:#e2543a;"></span> just written
  </div>

  <h3>Accesses by addressing mode (live)</h3>
  <div id="liveBars"></div>

  <h3>Live trace log</h3>
  <div class="trace-log">
    <table>
      <thead><tr><th>#</th><th>Instruction</th><th>Op</th><th>Addr</th><th>Value</th><th>Mode</th></tr></thead>
      <tbody id="traceBody"></tbody>
    </table>
  </div>
</div>

<script>
(function(){
  const MEM_SIZE = __MEM_SIZE__;
  const INITIAL_CELLS = __INITIAL_CELLS__;      // {"10": 99, ...}
  const INITIAL_REGISTERS = __INITIAL_REGISTERS__; // {"R0":0,...}
  const PROGRAM = __PROGRAM__;                  // [{opcode,mode,operand,dest_reg}, ...]
  const REGISTER_NAMES = __REGISTER_NAMES__;    // ["R0","R1","R2","R3"]

  let cells, registers, trace, accessCounts, halted, demoIndex, lastTouched, stepCounter;

  function freshState(){
    cells = new Array(MEM_SIZE).fill(0);
    for (const addr in INITIAL_CELLS){ cells[addr] = INITIAL_CELLS[addr]; }
    registers = Object.assign({}, INITIAL_REGISTERS);
    trace = [];
    accessCounts = {};
    halted = false;
    demoIndex = 0;
    lastTouched = {};
    stepCounter = 0;
  }
  freshState();

  function checkBounds(addr){
    if (!Number.isInteger(addr) || addr < 0 || addr >= MEM_SIZE){
      throw new Error("Memory address " + addr + " is outside the valid range 0-" + (MEM_SIZE-1) + ".");
    }
  }
  function memRead(addr, mode){
    checkBounds(addr);
    const value = cells[addr];
    trace.push(["READ", addr, value, mode]);
    accessCounts[mode] = (accessCounts[mode]||0) + 1;
    lastTouched[addr] = "read";
    return value;
  }
  function memWrite(addr, value, mode){
    checkBounds(addr);
    cells[addr] = value;
    trace.push(["WRITE", addr, value, mode]);
    accessCounts[mode] = (accessCounts[mode]||0) + 1;
    lastTouched[addr] = "write";
  }
  function regGet(name){
    if (!(name in registers)) throw new Error("Unknown register: " + name);
    return registers[name];
  }

  function effectiveAddress(mode, operand){
    if (mode === "IMMEDIATE") return [null, operand];
    if (mode === "DIRECT"){ const v = memRead(operand, "DIRECT"); return [operand, v]; }
    if (mode === "INDIRECT"){
      const real = memRead(operand, "INDIRECT");
      const v = memRead(real, "INDIRECT");
      return [real, v];
    }
    if (mode === "REGISTER") return [null, regGet("R"+operand)];
    if (mode === "REG_INDIRECT"){
      const addr = regGet("R"+operand);
      const v = memRead(addr, "REG_INDIRECT");
      return [addr, v];
    }
    if (mode === "INDEXED"){
      const baseReg = operand[0], offset = operand[1];
      const addr = regGet("R"+baseReg) + offset;
      const v = memRead(addr, "INDEXED");
      return [addr, v];
    }
    throw new Error("Unknown addressing mode: " + mode);
  }

  function storeEffective(mode, operand, value){
    if (mode === "DIRECT"){ memWrite(operand, value, "DIRECT"); return operand; }
    if (mode === "INDIRECT"){
      const real = memRead(operand, "INDIRECT");
      memWrite(real, value, "INDIRECT");
      return real;
    }
    if (mode === "REGISTER"){ registers["R"+operand] = value; return null; }
    if (mode === "REG_INDIRECT"){
      const addr = regGet("R"+operand);
      memWrite(addr, value, "REG_INDIRECT");
      return addr;
    }
    if (mode === "INDEXED"){
      const baseReg = operand[0], offset = operand[1];
      const addr = regGet("R"+baseReg) + offset;
      memWrite(addr, value, "INDEXED");
      return addr;
    }
    throw new Error("Cannot STORE using mode " + mode);
  }

  let historyRows = [];

  function instrText(instr){
    let opnd = instr.operand;
    if (Array.isArray(opnd)) opnd = "(" + opnd.join(", ") + ")";
    let t = instr.opcode + " " + instr.mode + " " + opnd;
    if (instr.dest_reg) t += " -> " + instr.dest_reg;
    return t;
  }

  function execute(instr){
    lastTouched = {};
    const traceStart = trace.length;
    let address = null, result = null;
    const op = instr.opcode;
    if (op === "LOAD"){
      const ea = effectiveAddress(instr.mode, instr.operand);
      registers[instr.dest_reg] = ea[1]; address = ea[0]; result = ea[1];
    } else if (op === "STORE"){
      const v = regGet(instr.dest_reg);
      address = storeEffective(instr.mode, instr.operand, v); result = v;
    } else if (op === "ADD"){
      const ea = effectiveAddress(instr.mode, instr.operand);
      registers[instr.dest_reg] = regGet(instr.dest_reg) + ea[1];
      address = ea[0]; result = registers[instr.dest_reg];
    } else if (op === "SUB"){
      const ea = effectiveAddress(instr.mode, instr.operand);
      registers[instr.dest_reg] = regGet(instr.dest_reg) - ea[1];
      address = ea[0]; result = registers[instr.dest_reg];
    } else if (op === "HLT"){
      halted = true;
    } else {
      throw new Error("Unsupported opcode in live panel: " + op);
    }
    stepCounter++;
    historyRows.push({ n: stepCounter, text: instrText(instr), caused: trace.slice(traceStart) });
    return { address: address, result: result };
  }

  // ---------- rendering ----------
  function renderRegs(){
    const el = document.getElementById("liveRegs");
    el.innerHTML = REGISTER_NAMES.map(function(r){
      return "<span><b>"+r+"</b> = "+registers[r]+"</span>";
    }).join("");
  }

  function renderMemGrid(){
    const el = document.getElementById("memGrid");
    let html = "";
    for (let i=0;i<MEM_SIZE;i++){
      let cls = "cell";
      if (lastTouched[i] === "read") cls += " touched-read";
      if (lastTouched[i] === "write") cls += " touched-write";
      html += '<div class="'+cls+'"><span class="a">'+i+'</span><span class="v">'+cells[i]+'</span></div>';
    }
    el.innerHTML = html;
  }

  function renderBars(){
    const el = document.getElementById("liveBars");
    const entries = Object.entries(accessCounts).sort(function(a,b){ return b[1]-a[1]; });
    if (entries.length === 0){
      el.innerHTML = "<p style='font-size:0.85rem;color:#5b6478;'>No memory accesses yet.</p>";
      return;
    }
    const max = Math.max.apply(null, entries.map(function(e){ return e[1]; }));
    el.innerHTML = entries.map(function(e){
      const mode = e[0], count = e[1];
      const pct = Math.round(100*count/max);
      return '<div class="bar-row"><div>'+mode+'</div><div class="bar-track"><div class="bar-fill" style="width:'+pct+'%"></div></div><div>'+count+'</div></div>';
    }).join("");
  }

  function renderTrace(){
    const body = document.getElementById("traceBody");
    let html = "";
    historyRows.forEach(function(h){
      if (h.caused.length === 0){
        html += '<tr><td>'+h.n+'</td><td>'+h.text+'</td><td colspan="4" style="color:#9aa1b1;">no data-memory access</td></tr>';
      } else {
        h.caused.forEach(function(c, idx){
          const label = idx===0 ? (h.n+'') : '';
          const instrCell = idx===0 ? h.text : '';
          html += '<tr><td>'+label+'</td><td>'+instrCell+'</td><td>'+c[0]+'</td><td>'+c[1]+'</td><td>'+c[2]+'</td><td>'+c[3]+'</td></tr>';
        });
      }
    });
    body.innerHTML = html;
    const wrap = body.closest(".trace-log");
    wrap.scrollTop = wrap.scrollHeight;
  }

  function renderAll(){
    renderRegs(); renderMemGrid(); renderBars(); renderTrace();
  }

  // ---------- demo stepper ----------
  function loadDemo(){
    freshState();
    historyRows = [];
    document.getElementById("btnStep").disabled = PROGRAM.length === 0;
    document.getElementById("demoStatus").textContent =
      "Demo program loaded (" + PROGRAM.length + " instructions). Click Step to execute one at a time.";
    renderAll();
  }
  function stepDemo(){
    if (halted || demoIndex >= PROGRAM.length){
      document.getElementById("btnStep").disabled = true;
      document.getElementById("demoStatus").textContent = "Program finished.";
      return;
    }
    const instr = PROGRAM[demoIndex];
    demoIndex++;
    try {
      execute(instr);
      document.getElementById("demoStatus").textContent =
        "Executed step " + demoIndex + " / " + PROGRAM.length + ": " + instrText(instr);
    } catch(e){
      document.getElementById("demoStatus").textContent = "Error: " + e.message;
    }
    if (halted || demoIndex >= PROGRAM.length) document.getElementById("btnStep").disabled = true;
    renderAll();
  }

  // ---------- custom instruction form ----------
  function updateOperandFields(){
    const mode = document.getElementById("inMode").value;
    const single = document.getElementById("operandSingleWrap");
    const baseReg = document.getElementById("operandRegWrap");
    const off = document.getElementById("operandOffWrap");
    if (mode === "INDEXED"){
      single.style.display = "none"; baseReg.style.display = ""; off.style.display = "";
    } else {
      single.style.display = ""; baseReg.style.display = "none"; off.style.display = "none";
    }
  }

  function runCustom(){
    const errEl = document.getElementById("runError");
    errEl.textContent = "";
    const opcode = document.getElementById("inOpcode").value;
    const mode = document.getElementById("inMode").value;
    const destReg = document.getElementById("inDestReg").value;
    let operand;
    if (mode === "INDEXED"){
      operand = [parseInt(document.getElementById("inBaseReg").value,10),
                 parseInt(document.getElementById("inOffset").value,10)];
    } else {
      operand = parseInt(document.getElementById("inOperand").value,10);
    }
    const instr = { opcode: opcode, mode: mode, operand: operand, dest_reg: (opcode==="HLT") ? null : destReg };
    try {
      execute(instr);
    } catch(e){
      errEl.textContent = e.message;
    }
    renderAll();
  }

  // ---------- wire up ----------
  document.getElementById("btnLoadDemo").addEventListener("click", loadDemo);
  document.getElementById("btnStep").addEventListener("click", stepDemo);
  document.getElementById("btnReset").addEventListener("click", function(){
    freshState(); historyRows = [];
    document.getElementById("btnStep").disabled = true;
    document.getElementById("demoStatus").textContent = "No program loaded yet.";
    document.getElementById("runError").textContent = "";
    renderAll();
  });
  document.getElementById("inMode").addEventListener("change", updateOperandFields);
  document.getElementById("btnRun").addEventListener("click", runCustom);

  const destSel = document.getElementById("inDestReg");
  destSel.innerHTML = REGISTER_NAMES.map(function(r){ return '<option>'+r+'</option>'; }).join("");

  updateOperandFields();
  renderAll();
})();
</script>
"""


def _interactive_panel_html(mem_size, initial_cells, initial_registers, program):
    program_json = json.dumps([
        {
            "opcode": instr.opcode,
            "mode": instr.mode,
            "operand": list(instr.operand) if isinstance(instr.operand, tuple) else instr.operand,
            "dest_reg": instr.dest_reg,
        }
        for instr in program
    ])
    html = INTERACTIVE_TEMPLATE
    html = html.replace("__MEM_SIZE__", str(mem_size))
    html = html.replace("__INITIAL_CELLS__", json.dumps(initial_cells))
    html = html.replace("__INITIAL_REGISTERS__", json.dumps(initial_registers))
    html = html.replace("__PROGRAM__", program_json)
    html = html.replace("__REGISTER_NAMES__", json.dumps(list(initial_registers.keys())))
    return html


def _registers_html(registers):
    spans = "".join(f"<span><b>{r}</b> = {v}</span>" for r, v in registers.items())
    return f'<div class="regs">{spans}</div>'


def _trace_table_html(mem_trace):
    rows = "".join(
        f"<tr><td>{op}</td><td>{addr}</td><td>{value}</td><td>{mode}</td></tr>"
        for op, addr, value, mode in mem_trace
    )
    return f"""
    <table>
      <tr><th>Op</th><th>Address</th><th>Value</th><th>Addressing mode</th></tr>
      {rows or '<tr><td colspan="4">No memory accesses recorded.</td></tr>'}
    </table>"""


def _history_table_html(history):
    rows = "".join(
        f"<tr><td>{instr}</td><td>{addr}</td><td>{result}</td></tr>"
        for instr, addr, result in history
    )
    return f"""
    <table>
      <tr><th>Instruction</th><th>Effective address</th><th>Result</th></tr>
      {rows}
    </table>"""


def _access_bars_html(access_count_by_mode):
    if not access_count_by_mode:
        return "<p>No memory accesses recorded.</p>"
    max_count = max(access_count_by_mode.values())
    rows = ""
    for mode, count in sorted(access_count_by_mode.items(), key=lambda kv: -kv[1]):
        pct = int(100 * count / max_count)
        rows += (
            f'<div class="bar-row"><div>{mode}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
            f"<div>{count}</div></div>"
        )
    return rows


def _test_table_html(program, history, expected_results):
    rows = ""
    for idx, mode, expected_addr, expected_value in expected_results:
        instr, obtained_addr, obtained_value = history[idx]
        passed = (obtained_addr == expected_addr) and (obtained_value == expected_value)
        css = "pass" if passed else "fail"
        label = "PASS" if passed else "FAIL"
        rows += (
            f"<tr><td>{idx}</td><td>{mode}</td><td>{expected_addr}</td><td>{obtained_addr}</td>"
            f'<td>{expected_value}</td><td>{obtained_value}</td><td class="{css}">{label}</td></tr>'
        )
    return f"""
    <table>
      <tr><th>#</th><th>Mode</th><th>Exp. addr</th><th>Obt. addr</th>
          <th>Exp. value</th><th>Obt. value</th><th>Result</th></tr>
      {rows}
    </table>"""


def generate_html(cpu, mem, program, expected_results,
                   initial_cells=None, initial_registers=None):
    """
    initial_cells / initial_registers: the *pre-run* snapshot (e.g. straight
    from test_programs.initial_memory_setup() / initial_registers()) so the
    live panel can start from the same clean state the static report shows
    the end result of. If omitted, the live panel just starts from all-zero
    memory and the CPU's current (already-run) registers.
    """
    if initial_cells is None:
        initial_cells = {}
    if initial_registers is None:
        initial_registers = dict(cpu.registers)

    interactive_html = _interactive_panel_html(
        mem.size, initial_cells, initial_registers, program
    )

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Simulator Run Report</title>{STYLE}</head>
<body><div class="wrap">
  <h1>Instruction &amp; Memory Access Simulator &mdash; Run Report</h1>

  <h2>Final registers (from this run)</h2>
  {_registers_html(cpu.registers)}

  <h2>Instruction-by-instruction results</h2>
  {_history_table_html(cpu.history)}

  <h2>Raw memory access trace</h2>
  {_trace_table_html(mem.trace)}

  <h2>Memory accesses by addressing mode</h2>
  {_access_bars_html(mem.access_count_by_mode)}

  <h2>Test cases (expected vs obtained)</h2>
  {_test_table_html(program, cpu.history, expected_results)}

  <h2>Try it yourself</h2>
  {interactive_html}

</div></body></html>"""
