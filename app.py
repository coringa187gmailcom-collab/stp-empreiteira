
def optimize_image(path, max_size=1600, quality=82):
    try:
        from PIL import Image
        img = Image.open(path)
        img = img.convert("RGB") if img.mode in ("RGBA", "P") else img
        # Resize if larger than max_size
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0]*ratio), int(img.size[1]*ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        # Save optimized
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, "JPEG", quality=quality, optimize=True)
        elif path.lower().endswith('.png'):
            img.save(path, "PNG", optimize=True)
        else:
            img.save(path, quality=quality, optimize=True)
    except Exception:
        pass

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import shutil
import io
import zipfile

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "stp-admin-secret-2026-change-me")

# Admin credentials (change these)
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "stp2026")

# Use volume if DATA_DIR is set, otherwise local static
DATA_DIR = os.environ.get("DATA_DIR", "")
if DATA_DIR:
    UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "papeleira"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, "pias"), exist_ok=True)
VIDEOS_FILE = os.path.join(UPLOAD_FOLDER, "videos.json")
if not os.path.exists(VIDEOS_FILE):
    with open(VIDEOS_FILE, "w") as f:
        json.dump([], f)

def load_videos():
    try:
        with open(VIDEOS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_videos(videos):
    with open(VIDEOS_FILE, "w") as f:
        json.dump(videos, f)

CATEGORIES_FILE = os.path.join(UPLOAD_FOLDER, "categories.json")
if not os.path.exists(CATEGORIES_FILE):
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(["papeleira", "pias", "nicho"], f)

def load_categories():
    try:
        with open(CATEGORIES_FILE) as f:
            cats = json.load(f)
    except:
        cats = ["papeleira", "pias", "nicho"]
    # Garantir que nicho sempre exista
    for required in ["papeleira", "pias", "nicho"]:
        if required not in cats:
            cats.append(required)
    return cats

def save_categories(cats):
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(cats, f)

SERVICES_FILE = os.path.join(UPLOAD_FOLDER, "services.json")
if not os.path.exists(SERVICES_FILE):
    default_services = [
        {"titulo": "Construção Civil", "descricao": "Obras residenciais e comerciais do zero, com acompanhamento completo."},
        {"titulo": "Reformas", "descricao": "Reformas residenciais e comerciais com acabamento de alta qualidade."},
        {"titulo": "Ampliações", "descricao": "Ampliação de imóveis com planejamento e execução profissional."}
    ]
    with open(SERVICES_FILE, "w") as f:
        json.dump(default_services, f)

def load_services():
    try:
        with open(SERVICES_FILE) as f:
            return json.load(f)
    except:
        return []

def save_services(services):
    with open(SERVICES_FILE, "w") as f:
        json.dump(services, f)

WORKS_FILE = os.path.join(UPLOAD_FOLDER, "works.json")
if not os.path.exists(WORKS_FILE):
    default_works = [
        {"titulo": "Construção Residencial", "imagem": "/static/images/obra1.jpg"},
        {"titulo": "Casa Moderna Entregue", "imagem": "/static/images/casa1.jpg"},
        {"titulo": "Estrutura de Concreto", "imagem": "/static/images/obra1.jpg"},
        {"titulo": "Fachada Contemporânea", "imagem": "/static/images/casa1.jpg"}
    ]
    with open(WORKS_FILE, "w") as f:
        json.dump(default_works, f)

def load_works():
    try:
        with open(WORKS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_works(works):
    with open(WORKS_FILE, "w") as f:
        json.dump(works, f)

PRICES_FILE = os.path.join(UPLOAD_FOLDER, "prices.json")
if not os.path.exists(PRICES_FILE):
    with open(PRICES_FILE, "w") as f:
        json.dump({}, f)

def load_prices():
    try:
        with open(PRICES_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_prices(prices):
    with open(PRICES_FILE, "w") as f:
        json.dump(prices, f)




def get_photos(cat):
    folder = os.path.join(UPLOAD_FOLDER, cat)
    if not os.path.exists(folder):
        return []
    prices = load_prices()
    result = []
    for f in os.listdir(folder):
        if allowed(f):
            key = f"{cat}/{f}"
            result.append({"url": f"/static/uploads/{cat}/{f}", "preco": prices.get(key, "")})
    return result



# Serve uploads from volume if needed
@app.route("/static/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

ALLOWED = {"png", "jpg", "jpeg", "webp", "gif"}

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

def is_admin():
    return session.get("admin") is True

@app.route("/")
def index():
    # Load all categories dynamically
    categories = load_categories()
    prices = load_prices()
    produtos = []
    for cat in categories:
        fotos = get_photos(cat)
        produtos.append({
            "nome": cat.replace("_", " ").title(),
            "slug": cat,
            "fotos": fotos,
            "preco": prices.get(cat, "")
        })
    services = load_services()
    works = load_works()
    return render_template("index.html", produtos=produtos, services=services, works=works)

# Hidden admin login
@app.route("/gestao-stp", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = request.form.get("usuario", "").strip()
        pwd = request.form.get("senha", "")
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session["admin"] = True
            session["admin_time"] = datetime.now().isoformat()
            flash("Login realizado.", "ok")
            return redirect(url_for("admin_panel"))
        flash("Usuário ou senha incorretos.", "erro")
    return render_template("admin_login.html")

@app.route("/gestao-stp/painel")
def admin_panel():
    if not is_admin():
        return redirect(url_for("admin_login"))
    categories = load_categories()
    prices = load_prices()
    produtos = []
    for cat in categories:
        folder = os.path.join(UPLOAD_FOLDER, cat)
        fotos = os.listdir(folder) if os.path.exists(folder) else []
        produtos.append({
            "nome": cat.replace("_", " ").title(),
            "slug": cat,
            "fotos": fotos,
            "preco": prices.get(cat, "")
        })
    videos = load_videos()
    services = load_services()
    works = load_works()
    return render_template("admin_panel.html", produtos=produtos, videos=videos, services=services, works=works)

@app.route("/gestao-stp/upload", methods=["POST"])
def admin_upload():
    if not is_admin():
        return redirect(url_for("admin_login"))
    categoria = request.form.get("categoria", "").strip().lower().replace(" ", "_")
    cats = load_categories()
    if categoria not in cats:
        flash("Categoria inválida.", "erro")
        return redirect(url_for("admin_panel"))
    files = request.files.getlist("fotos")
    saved = 0
    folder = os.path.join(app.static_folder, "uploads", categoria)
    os.makedirs(folder, exist_ok=True)
    for f in files:
        if f and f.filename and allowed(f.filename):
            name = secure_filename(f.filename)
            # avoid overwrite
            base, ext = os.path.splitext(name)
            final = name
            i = 1
            while os.path.exists(os.path.join(folder, final)):
                final = f"{base}_{i}{ext}"
                i += 1
            f.save(os.path.join(folder, final))
            saved += 1
    flash(f"{saved} foto(s) enviada(s) para {categoria}.", "ok")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/delete/<categoria>/<filename>", methods=["POST"])
def admin_delete(categoria, filename):
    if not is_admin():
        return redirect(url_for("admin_login"))
    if categoria not in load_categories():
        return redirect(url_for("admin_panel"))
    path = os.path.join(app.static_folder, "uploads", categoria, secure_filename(filename))
    if os.path.exists(path):
        os.remove(path)
        flash("Foto removida.", "ok")
    return redirect(url_for("admin_panel"))


@app.route("/gestao-stp/video", methods=["POST"])
def admin_video_add():
    if not is_admin():
        return redirect(url_for("admin_login"))
    titulo = request.form.get("titulo", "").strip()[:80]
    url = request.form.get("url", "").strip()
    if titulo and url:
        videos = load_videos()
        videos.append({"titulo": titulo, "url": url})
        save_videos(videos)
        flash("Vídeo adicionado.", "ok")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/video/delete/<int:idx>", methods=["POST"])
def admin_video_delete(idx):
    if not is_admin():
        return redirect(url_for("admin_login"))
    videos = load_videos()
    if 0 <= idx < len(videos):
        videos.pop(idx)
        save_videos(videos)
        flash("Vídeo removido.", "ok")
    return redirect(url_for("admin_panel"))


@app.route("/gestao-stp/backup")
def admin_backup():
    if not is_admin():
        return redirect(url_for("admin_login"))
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(UPLOAD_FOLDER):
            for file in files:
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, UPLOAD_FOLDER)
                zf.write(filepath, arcname)
    memory.seek(0)
    
def optimize_image(path, max_size=1600, quality=82):
    try:
        from PIL import Image
        img = Image.open(path)
        img = img.convert("RGB") if img.mode in ("RGBA", "P") else img
        # Resize if larger than max_size
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0]*ratio), int(img.size[1]*ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        # Save optimized
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, "JPEG", quality=quality, optimize=True)
        elif path.lower().endswith('.png'):
            img.save(path, "PNG", optimize=True)
        else:
            img.save(path, quality=quality, optimize=True)
    except Exception:
        pass

from flask import send_file
    return send_file(memory, download_name="stp-backup.zip", as_attachment=True, mimetype="application/zip")


@app.route("/gestao-stp/categoria", methods=["POST"])
def admin_create_category():
    if not is_admin():
        return redirect(url_for("admin_login"))
    nome = request.form.get("nome", "").strip()
    if nome:
        slug = nome.lower().replace(" ", "_")[:40]
        cats = load_categories()
        if slug not in cats:
            cats.append(slug)
            save_categories(cats)
            os.makedirs(os.path.join(UPLOAD_FOLDER, slug), exist_ok=True)
            flash(f"Card '{nome}' criado.", "ok")
        else:
            flash("Já existe um card com esse nome.", "erro")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/categoria/delete/<slug>", methods=["POST"])
def admin_delete_category(slug):
    if not is_admin():
        return redirect(url_for("admin_login"))
    cats = load_categories()
    if slug in cats and slug not in ("papeleira", "pias"):
        cats.remove(slug)
        save_categories(cats)
        flash("Card removido.", "ok")
    return redirect(url_for("admin_panel"))


@app.route("/gestao-stp/servico", methods=["POST"])
def admin_create_service():
    if not is_admin():
        return redirect(url_for("admin_login"))
    titulo = request.form.get("titulo", "").strip()[:80]
    descricao = request.form.get("descricao", "").strip()[:300]
    if titulo and descricao:
        services = load_services()
        services.append({"titulo": titulo, "descricao": descricao})
        save_services(services)
        flash("Serviço criado.", "ok")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/servico/delete/<int:idx>", methods=["POST"])
def admin_delete_service(idx):
    if not is_admin():
        return redirect(url_for("admin_login"))
    services = load_services()
    if 0 <= idx < len(services):
        services.pop(idx)
        save_services(services)
        flash("Serviço removido.", "ok")
    return redirect(url_for("admin_panel"))


@app.route("/gestao-stp/obra", methods=["POST"])
def admin_create_work():
    if not is_admin():
        return redirect(url_for("admin_login"))
    titulo = request.form.get("titulo", "").strip()[:80]
    files = request.files.getlist("foto")
    if titulo and files:
        folder = os.path.join(UPLOAD_FOLDER, "obras")
        os.makedirs(folder, exist_ok=True)
        works = load_works()
        added = 0
        for f in files:
            if f and f.filename and allowed(f.filename):
                name = secure_filename(f.filename)
                # Avoid overwrite
                base, ext = os.path.splitext(name)
                i = 1
                while os.path.exists(os.path.join(folder, name)):
                    name = f"{base}_{i}{ext}"
                    i += 1
                path = os.path.join(folder, name)
                f.save(path)
            optimize_image(path)
                works.append({"titulo": titulo, "imagem": f"/static/uploads/obras/{name}"})
                added += 1
        if added:
            save_works(works)
            flash(f"{added} foto(s) adicionada(s) à obra.", "ok")
        else:
            flash("Nenhuma foto válida enviada.", "erro")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/obra/edit/<int:idx>", methods=["POST"])
def admin_edit_work(idx):
    if not is_admin():
        return redirect(url_for("admin_login"))
    titulo = request.form.get("titulo", "").strip()[:80]
    works = load_works()
    if 0 <= idx < len(works) and titulo:
        works[idx]["titulo"] = titulo
        save_works(works)
        flash("Título atualizado.", "ok")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/obra/delete/<int:idx>", methods=["POST"])
def admin_delete_work(idx):
    if not is_admin():
        return redirect(url_for("admin_login"))
    works = load_works()
    if 0 <= idx < len(works):
        works.pop(idx)
        save_works(works)
        flash("Obra removida.", "ok")
    return redirect(url_for("admin_panel"))


@app.route("/gestao-stp/preco", methods=["POST"])
def admin_update_price():
    if not is_admin():
        return redirect(url_for("admin_login"))
    slug = request.form.get("slug", "").strip()
    preco = request.form.get("preco", "").strip()
    if slug:
        prices = load_prices()
        prices[slug] = preco
        save_prices(prices)
        flash("Valor atualizado.", "ok")
    return redirect(url_for("admin_panel"))


@app.route("/gestao-stp/preco", methods=["POST"])
def admin_set_price():
    if not is_admin():
        return redirect(url_for("admin_login"))
    key = request.form.get("key", "")
    preco = request.form.get("preco", "").strip()
    if key:
        prices = load_prices()
        if preco:
            prices[key] = preco
        else:
            prices.pop(key, None)
        save_prices(prices)
        flash("Valor atualizado.", "ok")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/sair")
def admin_logout():
    session.pop("admin", None)
    flash("Saiu do painel.", "ok")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
