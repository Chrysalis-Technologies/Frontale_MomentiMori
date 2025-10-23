# Placeholder Media Gallery

A lightweight Flask application that lets you upload images and videos, then share them through a simple gallery slideshow. Use the owner upload page to manage your collection, or share the guest upload link so others can contribute their own memories.

## Features

- 📤 Owner and guest upload forms with drag-friendly file inputs
- 🖼️ Automatically stores uploaded files in `static/uploads/`
- 🎞️ Bootstrap-powered slideshow gallery supporting images and videos
- 🔗 Share-friendly URLs for uploads and gallery viewing

## Getting Started

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the development server**
   ```bash
   flask --app app run --debug
   ```

3. **Open the app**
   - Owner upload page: <http://127.0.0.1:5000/upload>
   - Guest upload page: <http://127.0.0.1:5000/share/upload>
   - Public gallery: <http://127.0.0.1:5000/gallery>

## Configuration

Set `SECRET_KEY` in your environment if you want to override the default development key:

```bash
export SECRET_KEY="change-me"
```

You can adjust the maximum upload size by editing `app.config["MAX_CONTENT_LENGTH"]` in `app.py`.

## Folder Structure

```
.
├── app.py
├── requirements.txt
├── static
│   └── uploads
└── templates
    ├── base.html
    ├── gallery.html
    ├── shared_upload.html
    └── upload.html
```

## Notes

- The uploads directory is created automatically at runtime. Make sure the application has permission to write to it.
- This is a placeholder project name—you can rename the repository or adjust branding text at any time.
