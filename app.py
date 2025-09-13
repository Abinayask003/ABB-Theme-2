from flask import Flask, render_template, request, send_from_directory, flash
import os
from parser import generate_st_from_nl, save_st_file
import requests

app = Flask(__name__)
app.secret_key = "supersecret123"  

def check_internet():
    try:
        requests.get("https://api.openai.com", timeout=3)
        return True
    except:
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    st_code = ""
    st_filepath = ""
    llm_backend = os.environ.get("LLM_BACKEND", "ollama")

    if request.method == "POST":
        llm_backend = request.form.get("llm_backend", llm_backend)
        nl_instruction = request.form.get("nl_instruction", "").strip()
        batch_file = request.files.get("batch_file")

        # Warn if OpenAI is selected but no internet
        if llm_backend == "openai" and not check_internet():
            flash("Warning: OpenAI selected but no internet detected. Using fallback parser.")

        if batch_file and batch_file.filename != "":
            # Read file and split into lines
            text = batch_file.read().decode("utf-8")
            instructions = [line.strip() for line in text.splitlines() if line.strip()]

            st_blocks = []
            for i, instr in enumerate(instructions, 1):
                code_block = generate_st_from_nl(instr, backend=llm_backend)
                st_blocks.append(f"(* Instruction {i} *)\n{code_block}\n")

            st_code = "\n".join(st_blocks)
            st_filepath = save_st_file(st_code, "batch_output.st")

        elif nl_instruction:
            # Single instruction
            st_code = generate_st_from_nl(nl_instruction, backend=llm_backend)
            st_filepath = save_st_file(st_code, "single_output.st")

    return render_template(
        "index.html",
        st_code=st_code,
        st_filepath=st_filepath,
        llm_backend=llm_backend
    )

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("st_files", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
