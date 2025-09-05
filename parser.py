# parser.py
import os
import re
import subprocess
from typing import List

# Use official OpenAI Python client (modern interface)
# See README for environment variable configuration.
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")  # change to another model if you have access

def fallback_parse(nl_text: str) -> str:
    """
    Very simple deterministic fallback: create minimal ST logic from plain English
    by naive keyword detection (used if OpenAI call fails).
    """
    lines = [l.strip() for l in nl_text.splitlines() if l.strip()]
    st_lines = []
    for line in lines:
        # simple patterns
        m = re.match(r"(?i)start\s+(\w+)\s+when\s+(\w+)\s*<\s*(\d+\.?\d*)", line)
        if m:
            out, inp, val = m.groups()
            st_lines.append(f"IF {inp} < {val} THEN")
            st_lines.append(f"    {out} := TRUE;")
            st_lines.append("END_IF;")
            continue
        m = re.match(r"(?i)stop\s+(\w+)\s+when\s+(\w+)\s*>\s*(\d+\.?\d*)", line)
        if m:
            out, inp, val = m.groups()
            st_lines.append(f"IF {inp} > {val} THEN")
            st_lines.append(f"    {out} := FALSE;")
            st_lines.append("END_IF;")
            continue
        # generic fallback: turn into comment
        st_lines.append(f"// Could not parse: {line}")
    return "\n".join(st_lines) if st_lines else "// No logic generated (fallback)"

def detect_signals_from_text(text: str):
    """
    Naive signal detector. Returns (inputs:list, outputs:list).
    This is deliberately simple for demonstration; adjust for your domain names.
    """
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
    inputs = set()
    outputs = set()
    for t in tokens:
        if re.search(r"Level|LevelPct|Pct|Temp|Press|Pressure|Temperature", t, re.IGNORECASE):
            inputs.add(t)
        elif re.search(r"Reset|EStop|Start|Stop|Door|Fault|Motion|NoMotion", t, re.IGNORECASE):
            inputs.add(t)
        elif re.search(r"Pump|Valve|Motor|Alarm|Light|Buzzer|Fan|Cooling", t, re.IGNORECASE):
            outputs.add(t)
    # ensure common ones exist if none detected
    if not inputs:
        inputs.update(["Level", "Press"])
    if not outputs:
        outputs.update(["PumpCmd", "Alarm"])
    return list(inputs), list(outputs)

def wrap_into_pou(st_logic: str, inputs: List[str], outputs: List[str], program_name="plcprogram") -> str:
    """
    Build an OpenPLC-ready POU with VAR_INPUT and VAR_OUTPUT sections.
    If st_logic already contains VAR or PROGRAM, return as-is.
    """
    if re.search(r"\bVAR(_INPUT|_OUTPUT)?\b", st_logic, re.IGNORECASE) or re.search(r"\bPROGRAM\b", st_logic, re.IGNORECASE):
        return st_logic  # assume user/LLM has already provided full POU

    lines = []
    lines.append(f"PROGRAM {program_name}")
    if inputs:
        lines.append("VAR_INPUT")
        for v in inputs:
            lines.append(f"    {v} : REAL;")
        lines.append("END_VAR\n")
    if outputs:
        lines.append("VAR_OUTPUT")
        for v in outputs:
            lines.append(f"    {v} : BOOL;")
        lines.append("END_VAR\n")
    # add the logic and ensure statements end with semicolons where appropriate
    lines.append(st_logic.strip())
    lines.append("\nEND_PROGRAM")
    return "\n".join(lines)

def call_openai_for_st(nl_instruction: str) -> str:
    """
    Use OpenAI client to generate Structured Text logic. Returns text (ST body or full POU).
    Falls back to fallback_parse on any error.
    """
    # If OpenAI client can't be imported or API key missing, fallback
    if OpenAI is None or not OPENAI_API_KEY:
        return fallback_parse(nl_instruction)

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        # instruct the model to generate ST logic (without surrounding program headers ideally)
        prompt = f"""
You are an expert PLC programmer. Convert the following natural language instruction into IEC 61131-3 Structured Text (ST).
- Output only valid ST code (assignments use ':=' and statements end with semicolons).
- Do NOT include explanations.
- If possible produce only the logic statements (IF...END_IF; etc.). If variable declarations are needed, include VAR_INPUT/VAR_OUTPUT blocks.
Instruction:
{nl_instruction}
"""
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800,
        )
        # extract text
        content = ""
        try:
            content = resp.choices[0].message.content.strip()
        except Exception:
            # some responses may use different shapes; try to pull text
            content = getattr(resp, "output_text", "") or str(resp)
        if not content:
            return fallback_parse(nl_instruction)
        return content
    except Exception as e:
        # log to console and fallback
        print("OpenAI call failed:", e)
        return fallback_parse(nl_instruction)

def generate_st_from_nl(nl_instruction: str, program_name="plcprogram") -> str:
    """
    Full pipeline: call LLM to generate ST logic, detect variables, wrap into a POU and return final ST
    and also save into st_files/<timestamped>.st when calling app.
    """
    raw_st = call_openai_for_st(nl_instruction)
    # If LLM returned a full POU already, keep it. Otherwise detect signals and wrap.
    if re.search(r"\bPROGRAM\b|\bVAR(_INPUT|_OUTPUT)?\b", raw_st, re.IGNORECASE):
        final_st = raw_st
    else:
        inputs, outputs = detect_signals_from_text(nl_instruction + "\n" + raw_st)
        final_st = wrap_into_pou(raw_st, inputs, outputs, program_name=program_name)
    return final_st

def save_st_file(code: str, filename: str) -> str:
    """
    Save given ST code into st_files folder; return filepath.
    """
    os.makedirs("st_files", exist_ok=True)
    filepath = os.path.join("st_files", filename)
    with open(filepath, "w") as f:
        f.write(code)
    return filepath

def process_batch_file(filepath: str) -> List[str]:
    """
    Read a .txt with one instruction per line, convert each to ST and return list of ST strings.
    """
    results = []
    with open(filepath, "r") as f:
        for idx, line in enumerate(f, start=1):
            line=line.strip()
            if not line:
                continue
            st = generate_st_from_nl(line, program_name=f"plcprogram_{idx}")
            results.append(st)
            save_st_file(st, f"instruction_{idx}.st")
    return results

# Note: run_simulation left out here for brevity — you can reuse your prior plotting/simulator code and call it locally.
