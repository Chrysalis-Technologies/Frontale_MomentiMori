import os
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

import requests
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

import build_gallery

MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "/data/media"))
SITE_DIR = Path(os.getenv("SITE_DIR", "/app/site"))
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
ALLOWED_VIDEO_EXT = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".m4v"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXT.union(ALLOWED_VIDEO_EXT)
MAX_UPLOAD_MB = int(os.getenv("UPLOAD_MAX_MB", "500"))
CLIENT_ID = os.getenv("APPLICATION_CLIENT_ID")
CLIENT_SECRET = os.getenv("FRONTALE_UPLOADER_SECRET")
TENANT_ID = os.getenv("DIRECTORY_TENANT_ID")
TARGET_UPN = os.getenv("UPLOAD_TARGET_USER_UPN")
GRAPH_FOLDER = os.getenv("GRAPH_UPLOAD_FOLDER", "MemorialGalleryUploads")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "")
TOKEN_ENDPOINT = (
    f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    if TENANT_ID
    else None
)
GRAPH_SCOPE = "https://graph.microsoft.com/.default"

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

MEDIA_DIR.mkdir(parents=True, exist_ok=True)
SITE_DIR.mkdir(parents=True, exist_ok=True)

token_cache = {"token": None, "expires": 0.0}


def graph_enabled() -> bool:
    return all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, TARGET_UPN])


def allowed_file(filename: str) -> bool:
    return "." in filename and Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def get_graph_token() -> str:
    if not graph_enabled():
        raise RuntimeError("Graph credentials are not configured")
    now = time.time()
    if token_cache["token"] and now < token_cache["expires"] - 60:
        return token_cache["token"]
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": GRAPH_SCOPE,
        "grant_type": "client_credentials",
    }
    resp = requests.post(TOKEN_ENDPOINT, data=data, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    token_cache["token"] = payload["access_token"]
    token_cache["expires"] = now + payload.get("expires_in", 3600)
    return token_cache["token"]


def upload_to_onedrive(local_path: Path, remote_name: str) -> None:
    if not graph_enabled():
        return
    token = get_graph_token()
    clean_folder = GRAPH_FOLDER.strip("/") or "MemorialGalleryUploads"
    remote_path = f"{clean_folder}/{remote_name}"
    url = (
        "https://graph.microsoft.com/v1.0/users/"
        f"{TARGET_UPN}/drive/root:/{remote_path}:/content"
    )
    with local_path.open("rb") as stream:
        resp = requests.put(
            url,
            headers={"Authorization": f"Bearer {token}"},
            data=stream,
            timeout=300,
        )
    if resp.status_code >= 300:
        app.logger.warning("OneDrive upload failed (%s): %s", remote_name, resp.text)


def rebuild_site() -> None:
    build_gallery.main()


def ensure_site() -> None:
    if not (SITE_DIR / "index.html").exists():
        rebuild_site()


def save_files(files: Iterable) -> List[str]:
    saved: List[str] = []
    for storage in files:
        if not storage or storage.filename == "":
            continue
        if not allowed_file(storage.filename):
            flash(f"Unsupported file type: {storage.filename}", "warning")
            continue
        filename = secure_filename(storage.filename)
        ext = Path(filename).suffix.lower()
        unique_name = f"{int(time.time())}_{os.urandom(4).hex()}{ext}"
        dest = MEDIA_DIR / unique_name
        storage.save(dest)
        upload_to_onedrive(dest, unique_name)
        saved.append(unique_name)
    if saved:
        rebuild_site()
    return saved


def media_files() -> List[Path]:
    return [
        p
        for p in sorted(MEDIA_DIR.glob("*"), key=lambda f: f.stat().st_mtime, reverse=True)
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
    ]


def list_media() -> List[dict]:
    entries: List[dict] = []
    for path in media_files():
        entries.append(
            {
                "name": path.name,
                "url": url_for("serve_media", filename=path.name),
                "is_image": path.suffix.lower() in ALLOWED_IMAGE_EXT,
            }
        )
    return entries


@app.route("/")
def root():
    ensure_site()
    return send_from_directory(SITE_DIR, "index.html")


@app.route("/media/<path:filename>")
def serve_media(filename: str):
    return send_from_directory(MEDIA_DIR, filename)


@app.route("/site/<path:asset>")
def site_asset(asset: str):
    candidate = SITE_DIR / asset
    if candidate.is_file():
        return send_from_directory(SITE_DIR, asset)
    return ("Not Found", 404)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        files = request.files.getlist("media")
        if not files:
            flash("No files selected.", "warning")
        else:
            saved = save_files(files)
            if saved:
                flash(f"Uploaded {len(saved)} file(s).", "success")
            else:
                flash("No files were uploaded.", "danger")
        return redirect(url_for("upload"))
    return render_template(
        "upload.html",
        share_link=url_for("shared_upload", _external=True),
        gallery_link=url_for("gallery", _external=True),
        max_upload_mb=MAX_UPLOAD_MB,
    )


@app.route("/share/upload", methods=["GET", "POST"])
def shared_upload():
    if request.method == "POST":
        files = request.files.getlist("media")
        if not files:
            flash("No files selected.", "warning")
        else:
            saved = save_files(files)
            if saved:
                flash("Thanks! Your files are now waiting for review.", "success")
            else:
                flash("Your upload did not include any supported files.", "danger")
        return redirect(url_for("shared_upload"))
    return render_template("shared_upload.html", gallery_link=url_for("gallery", _external=True))


@app.route("/gallery")
def gallery():
    media_entries = list_media()
    return render_template("gallery.html", media_entries=media_entries)


@app.route("/healthz")
def healthz():
    return {"status": "ok", "media_count": len(media_files())}


@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


@app.after_request
def add_headers(resp):
    if PUBLIC_BASE_URL:
        resp.headers["Link"] = f"<{PUBLIC_BASE_URL}>; rel=canonical"
    return resp


@app.route("/<path:asset>")
def fallback(asset: str):
    candidate = SITE_DIR / asset
    if candidate.is_file():
        return send_from_directory(SITE_DIR, asset)
    return ("Not Found", 404)


if __name__ == "__main__":
    rebuild_site()
    app.run(host="0.0.0.0", port=8080)
