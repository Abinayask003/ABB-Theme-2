from flask import Flask, render_template, request, send_from_directory, flash
import os
from parser import generate_st_from_nl, save_st_file
import requests

app = Flask(__name__)
app.secret_key = "super_secret_key"  

# -------------------
# Helper: Check internet connection
# -------------------
def check_internet():
    try:
        requests.get("https://api.openai.com", timeout=3)
        return True
    except:
        return False

# -------------------
# Routes
# -------------------
@app.route("/", methods=["GET", "POST"])
def index():
    st_code = ""
    st_filepath = ""
    llm_backend = os.environ.get("LLM_BACKEND", "ollama")  # default if not set

    if request.method == "POST":
        # Read which backend user selected
        llm_backend = request.form.get("llm_backend", llm_backend)

        # Single instruction
        nl_instruction = request.form.get("nl_instruction", "").strip()

        # Batch file upload
        batch_file = request.files.get("batch_file")

        # Warn if user selected OpenAI but no internet
        if llm_backend == "openai" and not check_internet():
            flash("⚠️ Warning: OpenAI selected but no internet detected. Falling back to parser.")

        if batch_file and batch_file.filename != "":
            # Handle batch mode
            lines = [line.decode("utf-8").strip() for line in batch_file.read().splitlines()]
            generated_codes = []
            for idx, line in enumerate(lines, start=1):
                if not line:
                    continue
                st_code_each = generate_st_from_nl(line, program_name=f"plcprogram_{idx}", backend=llm_backend)
                save_st_file(st_code_each, f"instruction_{idx}.st")
                generated_codes.append(st_code_each)

            # Join all programs for display
            st_code = "\n\n".join(generated_codes)
            st_filepath = "batch_latest.st"
            save_st_file(st_code, st_filepath)

        elif nl_instruction:
            # Handle single instruction
            st_code = generate_st_from_nl(nl_instruction, backend=llm_backend)
            st_filepath = "latest.st"
            save_st_file(st_code, st_filepath)

    return render_template("index.html", st_code=st_code, st_filepath=st_filepath, llm_backend=llm_backend)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("st_files", filename, as_attachment=True)

# -------------------
# Main
# -------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
