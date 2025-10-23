import os
from datetime import datetime
from typing import Iterable
from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "webm", "mkv"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB limit per upload

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_files(files: Iterable) -> int:
    saved_count = 0
    for file in files:
        if not file or file.filename == "":
            continue
        if not allowed_file(file.filename):
            flash(f"File type not allowed: {file.filename}", "danger")
            continue
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}{ext}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(file_path)
        saved_count += 1
    if saved_count:
        flash(f"Successfully uploaded {saved_count} file(s).", "success")
    return saved_count


@app.route("/")
def home():
    return redirect(url_for("upload"))


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        files = request.files.getlist("media")
        if not files:
            flash("No files selected for upload.", "warning")
        else:
            save_files(files)
    return render_template(
        "upload.html",
        share_link=url_for("shared_upload", _external=True),
        gallery_link=url_for("gallery", _external=True),
    )


@app.route("/share/upload", methods=["GET", "POST"])
def shared_upload():
    if request.method == "POST":
        files = request.files.getlist("media")
        if not files:
            flash("No files selected for upload.", "warning")
        else:
            save_files(files)
    return render_template(
        "shared_upload.html",
        gallery_link=url_for("gallery", _external=True),
    )


@app.route("/gallery")
def gallery():
    media_files = sorted(os.listdir(app.config["UPLOAD_FOLDER"]))
    media_urls = [url_for("uploaded_file", filename=filename) for filename in media_files]
    return render_template("gallery.html", media_urls=media_urls)


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


if __name__ == "__main__":
    app.run(debug=True)
