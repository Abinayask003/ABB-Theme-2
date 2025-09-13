import os
import re
from typing import List

# LLM imports
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import ollama
except Exception:
    ollama = None

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
LLM_BACKEND = os.environ.get("LLM_BACKEND", "ollama")  # default backend

# -------------------
# Fallback parser
# -------------------
def fallback_parse(nl_text: str) -> str:
    """Simple keyword-based parser used if LLM is not available."""
    lines = [l.strip() for l in nl_text.splitlines() if l.strip()]
    st_lines = []
    for line in lines:
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
        st_lines.append(f"// Could not parse: {line}")
    return "\n".join(st_lines) if st_lines else "// No logic generated (fallback)"

# -------------------
# Signal detection & wrapper
# -------------------
def detect_signals_from_text(text: str):
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
    inputs, outputs = set(), set()
    for t in tokens:
        if re.search(r"Level|Temp|Press|Pressure", t, re.IGNORECASE):
            inputs.add(t)
        elif re.search(r"Reset|EStop|Start|Stop|Door|Fault|Motion", t, re.IGNORECASE):
            inputs.add(t)
        elif re.search(r"Pump|Valve|Motor|Alarm|Light|Buzzer|Fan|Cooling", t, re.IGNORECASE):
            outputs.add(t)
    if not inputs:
        inputs.update(["Level", "Press"])
    if not outputs:
        outputs.update(["PumpCmd", "Alarm"])
    return list(inputs), list(outputs)

def wrap_into_pou(st_logic: str, inputs: List[str], outputs: List[str], program_name="plcprogram") -> str:
    """Wrap logic into a valid CODESYS POU if not already wrapped."""
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
- Output only valid ST code (use ':=' for assignments, end each statement with ';').
- Do NOT include explanations.
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
    except Exception:
        return fallback_parse(nl_instruction)

def call_ollama(nl_instruction: str) -> str:
    if ollama is None:
        return fallback_parse(nl_instruction)
    try:
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": nl_instruction}]
        )
        return resp["message"]["content"].strip()
    except Exception:
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
        return st_logic
    inputs, outputs = detect_signals_from_text(nl_instruction + "\n" + st_logic)
    return wrap_into_pou(st_logic, inputs, outputs, program_name)

# -------------------
# Save to file
# -------------------
def save_st_file(code: str, filename: str) -> str:
    os.makedirs("st_files", exist_ok=True)
    filepath = os.path.join("st_files", filename)
    with open(filepath, "w") as f:
        f.write(code)
    return filepath
