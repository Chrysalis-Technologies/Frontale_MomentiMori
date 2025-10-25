# Frontale Momenti Mori - Dockerized Memorial Gallery

This repository now houses the dockerized memorial gallery that pairs with the Vivarium Orchestrator automation. The container watches a bind-mounted `media/` folder, generates thumbnails and optimized display assets with Pillow at container start, and serves a responsive gallery with a lightbox and slideshow.

## Highlights

- **Local tooling only** - Python 3.11 slim base, no telemetry, pinned deps.
- **Automatic processing** - Images get EXIF-aware rotation plus display/thumbnail variants; videos are copied and streamed inline.
- **Responsive UI** - CSS grid, keyboard controls, and a Play/Pause slideshow button driven by vanilla JS.
- **Docker-first workflow** - `docker compose up -d` handles build + serve; the writable layer caches processed assets for faster restarts.
- **LAN or public** - Run on your workstation, copy to any VPS, or drop behind Caddy/Traefik/Nginx with TLS.

## Repo layout

```
app/                # Docker build context (builder + entrypoint)
  build_gallery.py  # Media scanner + static-site generator
  Dockerfile
  entrypoint.sh
  requirements.txt
media/              # Place photos/videos here (gitignored, .gitkeep tracked)
site/               # Generated HTML/css/thumb cache (gitignored, .gitkeep tracked)
docker-compose.yml  # Builds/starts the memorial-gallery service
README.md
```

## Usage

1. **Collect media**
   - Drop JPG/PNG/WEBP or MP4/MOV/WebM files into `media/` (subfolders allowed).

2. **Build & run locally**
   ```powershell
   docker compose up -d --build
   ```
   - Browse http://localhost:8010/
   - Regenerate after changing media with `docker compose restart memorial-gallery`

3. **Stop**
   ```powershell
   docker compose down
   ```

### Deploying to a public host

1. Copy this repo (or just `app/`, `media/`, `site/`, `docker-compose.yml`) to your VPS: e.g., `scp -r Frontale_MomentiMori user@host:/opt/gallery`.
2. SSH in and run `docker compose up -d`. Make sure ports 8010/8080 are reachable or adjust the mapping in `docker-compose.yml`.
3. To expose via HTTPS, keep this container on an internal network and point your reverse proxy at `memorial-gallery:8080`. Example Caddy snippet:
   ```caddyfile
   memorial.example.com {
       reverse_proxy 127.0.0.1:8010
   }
   ```

## Customization

Environment variables in `docker-compose.yml` control the title, thumbnail/display geometry, and slideshow timing. Adjust them, run `docker compose up -d --build`, and the entrypoint will regenerate the static site with the new settings.

## Maintenance notes

- `media/` and `site/` are gitignored; keep the `.gitkeep` files so the folders stay in source control.
- Large deployments should periodically archive `site/` if it grows beyond a few hundred MB; deleting it is safe because the next container start rebuilds everything.
- If you tweak `app/build_gallery.py`, rebuild with `docker compose build --no-cache memorial-gallery && docker compose up -d` so Pillow recompiles as needed.

This repo replaces the earlier Flask uploader prototype, which wasn’t required for the Dockerized gallery workflow.
