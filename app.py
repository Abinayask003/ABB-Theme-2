# app.py
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from parser import generate_st_from_nl, save_st_file, process_batch_file
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")
UPLOAD_FOLDER = "st_files"
ALLOWED_EXTENSIONS = {"txt"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET","POST"])
def index():
    st_code = ""
    st_filepath = ""
    if request.method == "POST":
        mode = request.form.get("mode")
        if mode == "single":
            nl_instruction = request.form.get("nl_instruction","").strip()
            if not nl_instruction:
                flash("Please enter an instruction")
                return redirect(url_for("index"))
            st_code = generate_st_from_nl(nl_instruction, program_name="plcprogram")
            st_filepath = save_st_file(st_code, "instruction.st")
        elif mode == "batch":
            uploaded_file = request.files.get("batch_file")
            if not (uploaded_file and allowed_file(uploaded_file.filename)):
                flash("Please upload a .txt file for batch.")
                return redirect(url_for("index"))
            filename = secure_filename(uploaded_file.filename)
            saved_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(saved_path)
            st_list = process_batch_file(saved_path)
            st_code = "\n\n".join(st_list)
            st_filepath = save_st_file(st_code, "batch_instructions.st")
    return render_template("index.html", st_code=st_code, st_filepath=st_filepath)

@app.route("/download/<filename>")
def download(filename):
    filepath = os.path.join("st_files", filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    flash("File not found")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
