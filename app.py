from flask import Flask, render_template, request, send_from_directory, flash
import os
from parser import generate_st_from_nl, save_st_file
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"

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
        llm_backend = request.form.get("llm_backend")
        nl_instruction = request.form.get("nl_instruction", "")
        batch_file = request.files.get("batch_file")

        if llm_backend == "openai" and not check_internet():
            flash("Warning: OpenAI selected but no internet detected. Using fallback parser.")

        if batch_file and batch_file.filename != "":
            lines = [line.decode("utf-8").strip() for line in batch_file.read().splitlines()]
            st_code = "\n\n".join([generate_st_from_nl(line, backend=llm_backend) for line in lines])
        else:
            st_code = generate_st_from_nl(nl_instruction, backend=llm_backend)

        st_filepath = save_st_file(st_code, "latest.st")

    return render_template("index.html", st_code=st_code, st_filepath=st_filepath, llm_backend=llm_backend)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("st_files", filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
