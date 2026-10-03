import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from utils.parser import extract_text
from utils.analyzer import analyze_resume, match_with_jd

app = Flask(__name__)
app.secret_key = "resumeiq-secret-key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
ALLOWED = {"pdf", "docx", "txt"}
os.makedirs("uploads", exist_ok=True)


def read_upload(file):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    path = os.path.join(app.config["UPLOAD_FOLDER"],
                        f"{uuid.uuid4().hex}_{secure_filename(file.filename)}")
    file.save(path)
    try:
        return extract_text(path), ext
    finally:
        os.remove(path)


def allowed(name):
    return "." in name and name.rsplit(".", 1)[-1].lower() in ALLOWED


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("resume")
    if not file or not allowed(file.filename):
        flash("Please upload a PDF, DOCX or TXT file.")
        return redirect(url_for("index"))
    text, _ = read_upload(file)
    if len(text) < 50:
        flash("Could not read text from the file. Try another resume.")
        return redirect(url_for("index"))
    return render_template("result.html", r=analyze_resume(text))


@app.route("/recruiter", methods=["GET", "POST"])
def recruiter():
    result = None
    if request.method == "POST":
        file = request.files.get("resume")
        jd = request.form.get("jd", "")
        if file and allowed(file.filename) and jd.strip():
            text, _ = read_upload(file)
            result = match_with_jd(text, jd)
        else:
            flash("Upload a resume and paste the job description.")
    return render_template("recruiter.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)