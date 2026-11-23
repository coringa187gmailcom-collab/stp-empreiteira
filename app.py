from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os
from werkzeug.utils import secure_filename
from datetime import datetime

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
    # Load uploaded photos
    papeleira = []
    pias = []
    base = app.static_folder + "/uploads"
    if os.path.exists(base + "/papeleira"):
        papeleira = [f"/static/uploads/papeleira/{f}" for f in os.listdir(base + "/papeleira") if allowed(f)]
    if os.path.exists(base + "/pias"):
        pias = [f"/static/uploads/pias/{f}" for f in os.listdir(base + "/pias") if allowed(f)]
    return render_template("index.html", papeleira=papeleira, pias=pias)

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
    papeleira = []
    pias = []
    base = os.path.join(app.static_folder, "uploads")
    if os.path.exists(os.path.join(base, "papeleira")):
        papeleira = os.listdir(os.path.join(base, "papeleira"))
    if os.path.exists(os.path.join(base, "pias")):
        pias = os.listdir(os.path.join(base, "pias"))
    return render_template("admin_panel.html", papeleira=papeleira, pias=pias)

@app.route("/gestao-stp/upload", methods=["POST"])
def admin_upload():
    if not is_admin():
        return redirect(url_for("admin_login"))
    categoria = request.form.get("categoria")
    if categoria not in ("papeleira", "pias"):
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
    if categoria not in ("papeleira", "pias"):
        return redirect(url_for("admin_panel"))
    path = os.path.join(app.static_folder, "uploads", categoria, secure_filename(filename))
    if os.path.exists(path):
        os.remove(path)
        flash("Foto removida.", "ok")
    return redirect(url_for("admin_panel"))

@app.route("/gestao-stp/sair")
def admin_logout():
    session.pop("admin", None)
    flash("Saiu do painel.", "ok")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
