import os, sys, json, re, shutil, hashlib
from pathlib import Path
from PIL import Image, ImageOps

MEDIA_DIR = os.getenv("MEDIA_DIR", "/data/media")
SITE_DIR = os.getenv("SITE_DIR", "/app/site")
TITLE = os.getenv("TITLE", "Memorial Gallery")
THUMB = int(os.getenv("THUMBNAIL_MAX_PX", "480"))
DISPLAY = int(os.getenv("DISPLAY_MAX_PX", "1280"))
SLIDE = int(os.getenv("SLIDESHOW_INTERVAL_SEC", "6"))

IMG_EXT = {".jpg",".jpeg",".png",".bmp",".gif",".webp"}
VID_EXT = {".mp4",".webm",".mov",".m4v",".avi"}

def ensure_dirs():
    Path(SITE_DIR).mkdir(parents=True, exist_ok=True)
    for d in ("thumbs","images","videos"):
        Path(SITE_DIR, d).mkdir(parents=True, exist_ok=True)

def safe_name(p: Path) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", p.stem)
    h = hashlib.sha1(str(p).encode("utf-8")).hexdigest()[:8]
    return f"{base}_{h}"

def process_image(src: Path):
    name = safe_name(src)
    img = Image.open(src)
    img = ImageOps.exif_transpose(img).convert("RGB")
    d = img.copy(); d.thumbnail((DISPLAY, DISPLAY))
    t = img.copy(); t.thumbnail((THUMB, THUMB))
    disp = Path(SITE_DIR,"images",f"{name}.jpg")
    thum = Path(SITE_DIR,"thumbs",f"{name}.jpg")
    d.save(disp, "JPEG", quality=85, optimize=True)
    t.save(thum, "JPEG", quality=80, optimize=True)
    return {"type":"image","title":src.stem,
            "src":str(disp.relative_to(SITE_DIR)).replace("\\","/"),
            "thumb":str(thum.relative_to(SITE_DIR)).replace("\\","/")}

def process_video(src: Path):
    name = safe_name(src) + src.suffix.lower()
    dst = Path(SITE_DIR,"videos",name)
    shutil.copy2(src, dst)
    return {"type":"video","title":src.stem,
            "src":str(dst.relative_to(SITE_DIR)).replace("\\","/"),
            "thumb":""}

def scan_items():
    items=[]
    root = Path(MEDIA_DIR)
    if not root.exists():
        return items
    for p in root.rglob("*"):
        if not p.is_file(): continue
        ext = p.suffix.lower()
        try:
            if ext in IMG_EXT: items.append(process_image(p))
            elif ext in VID_EXT: items.append(process_video(p))
        except Exception as e:
            print(f"Skipping {p}: {e}", file=sys.stderr)
    items.sort(key=lambda x: x["title"].lower())
    return items

def write_index(items):
    data_json = json.dumps(items, ensure_ascii=False)
    css = """body{margin:0;font-family:system-ui,Segoe UI,Arial,sans-serif;background:#0b0c10;color:#eee}
header{padding:12px 16px;background:#111;position:sticky;top:0;z-index:3;border-bottom:1px solid #222;display:flex;align-items:center;justify-content:space-between;gap:12px}
h1{margin:0;font-size:18px}
.cta{color:#fff;background:#2d7cff;border-radius:999px;padding:8px 16px;text-decoration:none;font-size:13px;font-weight:600;transition:background .2s}
.cta:hover{background:#3c8bff}
main{padding:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
.card{cursor:pointer;border-radius:8px;overflow:hidden;background:#151515}
.card img,.card video{width:100%;height:160px;object-fit:cover;display:block}
.card .label{padding:6px 8px;font-size:12px;color:#ccc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lb{position:fixed;inset:0;background:rgba(0,0,0,.92);display:none;align-items:center;justify-content:center;z-index:10}
.lb.show{display:flex}
.lb .inner{max-width:95vw;max-height:90vh;text-align:center}
.lb img,.lb video{max-width:95vw;max-height:85vh}
.controls{position:fixed;bottom:16px;left:0;right:0;display:flex;gap:8px;justify-content:center}
button{background:#222;color:#ddd;border:1px solid #333;border-radius:6px;padding:8px 12px;font-size:14px;cursor:pointer}
button:hover{background:#2a2a2a}"""
    js = f"""const DATA=JSON.parse(document.getElementById('data').textContent);
const INTERVAL={SLIDE}*1000;
const grid=document.getElementById('grid');
const lb=document.getElementById('lb'), inner=document.getElementById('lb-inner');
const btnPrev=document.getElementById('prev'), btnNext=document.getElementById('next');
const btnPlay=document.getElementById('play'), btnClose=document.getElementById('close');
let idx=-1,timer=null;
function node(html){{const t=document.createElement('template');t.innerHTML=html.trim();return t.content.firstChild;}}
function card(it,i){{
  const media = it.type==='image' ? `<img loading="lazy" src="${{it.thumb||it.src}}" alt="">`
                                  : `<video preload="metadata" src="${{it.src}}"></video>`;
  const el=node(`<div class="card" data-i="${{i}}">${{media}}<div class="label">${{it.title}}</div></div>`);
  el.onclick=()=>open(i); return el;
}}
DATA.forEach((it,i)=>grid.appendChild(card(it,i)));
function open(i){{
  idx=(i+DATA.length)%DATA.length;
  const it=DATA[idx];
  inner.innerHTML = it.type==='image' ? `<img src="${{it.src}}" alt="">`
                                      : `<video src="${{it.src}}" controls autoplay></video>`;
  lb.classList.add('show');
}}
function close(){{lb.classList.remove('show'); stop();}}
function next(){{open(idx+1);}}
function prev(){{open(idx-1);}}
function play(){{ if(timer){{stop();}} else {{timer=setInterval(next,INTERVAL); btnPlay.textContent='Pause';}}}}
function stop(){{ if(timer){{clearInterval(timer); timer=null;}} btnPlay.textContent='Play';}}
btnNext.onclick=next; btnPrev.onclick=prev; btnPlay.onclick=play; btnClose.onclick=close;
window.addEventListener('keydown',e=>{{ if(e.key==='Escape') close(); if(e.key==='ArrowRight') next(); if(e.key==='ArrowLeft') prev(); }});
lb.addEventListener('click',e=>{{ if(e.target===lb) close(); }});
"""
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title><style>{css}</style></head>
<body><header><h1>{TITLE}</h1><a class="cta" href="/upload">Share a Memory</a></header><main><div id="grid" class="grid"></div></main>
<div id="lb" class="lb"><div class="inner" id="lb-inner"></div></div>
<div class="controls">
  <button id="prev" aria-label="Previous">⟨ Prev</button>
  <button id="play" aria-label="Play/Pause">Play</button>
  <button id="next" aria-label="Next">Next ⟩</button>
  <button id="close" aria-label="Close">Close ✕</button>
</div>
<script id="data" type="application/json">{data_json}</script>
<script>{js}</script></body></html>"""
    Path(SITE_DIR,"index.html").write_text(html, encoding="utf-8")

def main():
    ensure_dirs()
    items = scan_items()
    write_index(items)
    print(f"Built {len(items)} items into {SITE_DIR}")

if __name__=="__main__":
    if "--dry-run" in sys.argv:
        ensure_dirs(); print(f"DRY RUN: would scan {MEDIA_DIR} and write {SITE_DIR}"); sys.exit(0)
    main()
