# parser.py
import os
import re
from typing import List

# LLM imports
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from ollama import Client as OllamaClient
except Exception:
    OllamaClient = None

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
LLM_BACKEND = os.environ.get("LLM_BACKEND", "ollama")

# -------------------
# Fallback parser (basic regex-based rules)
# -------------------
def fallback_parse(nl_text: str) -> str:
    """
    Rule-based fallback parser: converts common patterns like
    start/stop/turn on/off, >, <, after seconds, and/or conditions.
    """
    lines = [l.strip() for l in nl_text.splitlines() if l.strip()]
    st_lines = []

    for line in lines:
        # Turn on / Start when < value
        m = re.match(r"(?i)(start|turn on)\s+(\w+)\s+when\s+(\w+)\s*<\s*(\d+\.?\d*)", line)
        if m:
            _, out, inp, val = m.groups()
            st_lines.append(f"IF {inp} < {val} THEN")
            st_lines.append(f"    {out} := TRUE;")
            st_lines.append("ELSE")
            st_lines.append(f"    {out} := FALSE;")
            st_lines.append("END_IF;")
            continue

        # Stop / Turn off when > value
        m = re.match(r"(?i)(stop|turn off)\s+(\w+)\s+when\s+(\w+)\s*>\s*(\d+\.?\d*)", line)
        if m:
            _, out, inp, val = m.groups()
            st_lines.append(f"IF {inp} > {val} THEN")
            st_lines.append(f"    {out} := FALSE;")
            st_lines.append("ELSE")
            st_lines.append(f"    {out} := TRUE;")
            st_lines.append("END_IF;")
            continue

        # After X seconds (simple timer placeholder)
        m = re.match(r"(?i)(start|turn on)\s+(\w+)\s+after\s+(\d+)\s*sec", line)
        if m:
            _, out, delay = m.groups()
            st_lines.append(f"// Timer logic placeholder: {out} turns on after {delay} sec")
            st_lines.append(f"{out} := TRUE;")
            continue

        # AND / OR logic
        m = re.match(r"(?i)(start|turn on)\s+(\w+)\s+when\s+(.+)", line)
        if m:
            _, out, cond = m.groups()
            cond = cond.replace(" and ", " AND ").replace(" or ", " OR ")
            st_lines.append(f"IF {cond} THEN")
            st_lines.append(f"    {out} := TRUE;")
            st_lines.append("ELSE")
            st_lines.append(f"    {out} := FALSE;")
            st_lines.append("END_IF;")
            continue

        st_lines.append(f"// Could not parse: {line}")

    return "\n".join(st_lines) if st_lines else "// No logic generated (fallback)"

# -------------------
# Signal detection
# -------------------
def detect_signals_from_text(text: str):
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
    inputs, outputs = set(), set()
    for t in tokens:
        if re.search(r"Level|Temp|Press|Pressure|Sensor|Time|Delay", t, re.IGNORECASE):
            inputs.add(t)
        elif re.search(r"Start|Stop|Reset|Button|Switch", t, re.IGNORECASE):
            inputs.add(t)
        elif re.search(r"Pump|Valve|Motor|Alarm|Light|Buzzer|Fan|Cooling", t, re.IGNORECASE):
            outputs.add(t)
    if not inputs:
        inputs.update(["Level", "Press"])
    if not outputs:
        outputs.update(["PumpCmd", "Alarm"])
    return list(inputs), list(outputs)

# -------------------
# Wrap into POU
# -------------------
def wrap_into_pou(st_logic: str, inputs: List[str], outputs: List[str], program_name="plcprogram") -> str:
    if re.search(r"\bVAR(_INPUT|_OUTPUT)?\b", st_logic, re.IGNORECASE) or re.search(r"\bPROGRAM\b", st_logic, re.IGNORECASE):
        return st_logic
    lines = [f"PROGRAM {program_name}"]
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
    lines.append(st_logic.strip())
    lines.append("\nEND_PROGRAM")
    return "\n".join(lines)

# -------------------
# LLM Calls
# -------------------
def call_openai(nl_instruction: str) -> str:
    if OpenAI is None or not OPENAI_API_KEY:
        return fallback_parse(nl_instruction)
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"""
You are an expert PLC programmer. Convert the following natural language instruction into IEC 61131-3 Structured Text (ST).

Guidelines:
- Always implement **all conditions** (start, stop, turn on/off, timers, AND/OR, etc.).
- Every IF must include an ELSE to ensure defined outputs.
- Valid syntax only: ':=' for assignments, ';' at end, END_IF; after IF.
- No explanations, only ST code.

Instruction:
{nl_instruction}
"""
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI call failed:", e)
        return fallback_parse(nl_instruction)

def call_ollama(nl_instruction: str) -> str:
    if OllamaClient is None:
        return fallback_parse(nl_instruction)
    try:
        client = OllamaClient()
        prompt = f"""
You are an expert PLC programmer. Convert the following natural language instruction into IEC 61131-3 Structured Text (ST).

Guidelines:
- Always implement **all conditions** (start, stop, turn on/off, timers, AND/OR, etc.).
- Every IF must include an ELSE to ensure defined outputs.
- Valid syntax only: ':=' for assignments, ';' at end, END_IF; after IF.
- No explanations, only ST code.

Instruction:
{nl_instruction}
"""
        resp = client.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        if isinstance(resp, dict) and "message" in resp:
            return resp["message"]["content"].strip()
        elif isinstance(resp, dict) and "content" in resp:
            return resp["content"].strip()
        return str(resp)
    except Exception as e:
        print("Ollama call failed:", e)
        return fallback_parse(nl_instruction)

# -------------------
# Main generator
# -------------------
def generate_st_from_nl(nl_instruction: str, program_name="plcprogram", backend=None) -> str:
    backend = backend or LLM_BACKEND
    if backend == "openai":
        st_logic = call_openai(nl_instruction)
    else:
        st_logic = call_ollama(nl_instruction)

    if re.search(r"\bPROGRAM\b|\bVAR(_INPUT|_OUTPUT)?\b", st_logic, re.IGNORECASE):
        final_st = st_logic
    else:
        inputs, outputs = detect_signals_from_text(nl_instruction + "\n" + st_logic)
        final_st = wrap_into_pou(st_logic, inputs, outputs, program_name)
    return final_st

# -------------------
# Save to file
# -------------------
def save_st_file(code: str, filename: str) -> str:
    os.makedirs("st_files", exist_ok=True)
    filepath = os.path.join("st_files", filename)
    with open(filepath, "w") as f:
        f.write(code)
    return filepath
