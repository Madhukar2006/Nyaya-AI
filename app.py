import logging
import secrets
import uuid
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from config import GEMINI_API_KEY, SECRET_KEY
from database.db import get_db, init_db
from services.ai_service import analyze_legal_document, get_legal_response

# AI assistance: ChatGPT/Codex helped draft and debug parts of this application.
# Madhukar Pal reviewed and adapted the implementation for the NyayaAI project.
app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "docx"}
init_db()


def current_user():
    if "user_id" not in session:
        return None
    db = get_db()
    user = db.execute(
        "SELECT id, username, email, created_at FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    db.close()
    if user is None:
        session.clear()
    return user


def login_required():
    if current_user() is None:
        return redirect(url_for("login"))
    return None


@app.context_processor
def template_context():
    return {"nav_user": current_user(), "csrf_token": session.get("csrf_token", "")}


@app.before_request
def protect_forms():
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    if request.method == "POST":
        submitted = request.form.get("csrf_token", "")
        if not secrets.compare_digest(submitted, session["csrf_token"]):
            abort(400)


def extract_document_text(path, extension):
    if extension in {"txt", "md"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if extension == "pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if extension == "docx":
        from zipfile import ZipFile
        from xml.etree import ElementTree
        with ZipFile(path) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
        return "\n".join(
            "".join(node.itertext()) for node in root.iter()
            if node.tag.endswith("}p")
        )
    raise ValueError("Unsupported document type")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("Please complete every field.", "error")
        elif len(username) > 40 or len(email) > 254 or "@" not in email:
            flash("Please enter a valid username and email address.", "error")
        elif password != request.form.get("confirmation", ""):
            flash("The passwords do not match.", "error")
        elif len(password) < 8:
            flash("Choose a password with at least 8 characters.", "error")
        else:
            db = get_db()
            exists = db.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
            ).fetchone()
            if exists:
                db.close()
                flash("That username or email is already registered.", "error")
            else:
                db.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password)),
                )
                db.commit()
                db.close()
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
        return redirect(url_for("register"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        db.close()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Email or password was not recognized.", "error")
            return redirect(url_for("login"))
        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    denied = login_required()
    if denied:
        return denied
    user = current_user()
    db = get_db()
    history = db.execute(
        "SELECT id, title, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 5",
        (user["id"],),
    ).fetchall()
    db.close()
    return render_template("dashboard.html", user=user, history=history)


@app.route("/chat", methods=["GET", "POST"])
def chat():
    denied = login_required()
    if denied:
        return denied
    user = current_user()
    db = get_db()
    error_message = None
    conversation_id = request.args.get("conversation", type=int)

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        conversation_id = request.form.get("conversation_id", type=int)
        if not message:
            flash("Type a question before sending it.", "error")
            db.close()
            return redirect(url_for("chat", conversation=conversation_id) if conversation_id else url_for("chat"))
        if len(message) > 2000:
            message = message[:2000]
        conversation = None
        if conversation_id:
            conversation = db.execute(
                "SELECT id FROM conversations WHERE id = ? AND user_id = ?",
                (conversation_id, user["id"]),
            ).fetchone()
            if conversation is None:
                db.close()
                abort(404)
        else:
            title = " ".join(message.split())[:60]
            cursor = db.execute(
                "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
                (user["id"], title or "New conversation"),
            )
            conversation_id = cursor.lastrowid
        db.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'user', ?)",
            (conversation_id, message),
        )
        db.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
        db.commit()
        prior = db.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT 12",
            (conversation_id,),
        ).fetchall()
        prompt = "\n\n".join(f"{item['role'].title()}: {item['content']}" for item in reversed(prior))
        try:
            answer = get_legal_response(prompt)
            db.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, 'assistant', ?)",
                (conversation_id, answer),
            )
            db.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
            db.commit()
        except Exception as error:
            detail = str(error)
            if GEMINI_API_KEY:
                detail = detail.replace(GEMINI_API_KEY, "[REDACTED]")
            logger.error("Gemini request failed (%s): %s", type(error).__name__, detail)
            error_message = "NyayaAI could not connect to the AI service right now. Please try again later."
        return redirect(url_for("chat", conversation=conversation_id, error="service" if error_message else None))

    conversation = None
    messages = []
    if conversation_id:
        conversation = db.execute(
            "SELECT id, title FROM conversations WHERE id = ? AND user_id = ?",
            (conversation_id, user["id"]),
        ).fetchone()
        if conversation is None:
            db.close()
            abort(404)
        messages = db.execute(
            "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id",
            (conversation_id,),
        ).fetchall()
    if request.args.get("error") == "service":
        error_message = "NyayaAI could not connect to the AI service right now. Please try again later."
    conversations = db.execute(
        "SELECT id, title FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 12",
        (user["id"],),
    ).fetchall()
    db.close()
    return render_template("chat.html", conversation=conversation, messages=messages,
                           conversations=conversations, error_message=error_message)


@app.post("/history/<int:conversation_id>/delete")
def delete_conversation(conversation_id):
    denied = login_required()
    if denied:
        return denied
    db = get_db()
    db.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, session["user_id"]))
    db.commit()
    db.close()
    flash("Conversation deleted.", "success")
    return redirect(url_for("history"))


@app.route("/history")
def history():
    denied = login_required()
    if denied:
        return denied
    db = get_db()
    conversations = db.execute(
        "SELECT c.id, c.title, c.created_at, c.updated_at, COUNT(m.id) AS message_count "
        "FROM conversations c LEFT JOIN messages m ON c.id = m.conversation_id "
        "WHERE c.user_id = ? GROUP BY c.id ORDER BY c.updated_at DESC",
        (session["user_id"],),
    ).fetchall()
    db.close()
    return render_template("history.html", conversations=conversations)


@app.route("/documents", methods=["GET", "POST"])
def documents():
    denied = login_required()
    if denied:
        return denied
    user = current_user()
    db = get_db()
    selected = request.args.get("id", type=int)
    if request.method == "POST":
        upload = request.files.get("document")
        if upload is None or not upload.filename:
            flash("Choose a file to upload.", "error")
            db.close()
            return redirect(url_for("documents"))
        safe_name = secure_filename(upload.filename)
        extension = Path(safe_name).suffix.lower().lstrip(".")
        if extension not in ALLOWED_EXTENSIONS:
            flash("Upload a PDF, DOCX, TXT, or Markdown file.", "error")
            db.close()
            return redirect(url_for("documents"))
        user_dir = UPLOAD_DIR / str(user["id"])
        user_dir.mkdir(parents=True, exist_ok=True)
        stored_path = user_dir / f"{uuid.uuid4().hex}.{extension}"
        upload.save(stored_path)
        try:
            extracted = extract_document_text(stored_path, extension)[:100000]
        except Exception as error:
            logger.warning("Document extraction failed (%s)", type(error).__name__)
            stored_path.unlink(missing_ok=True)
            flash("We could not read this file. Check that it is a valid, text-based document.", "error")
            db.close()
            return redirect(url_for("documents"))
        if not extracted.strip():
            stored_path.unlink(missing_ok=True)
            flash("No readable text was found in this document.", "error")
            db.close()
            return redirect(url_for("documents"))
        cursor = db.execute(
            "INSERT INTO documents (user_id, original_name, stored_name, extracted_text) VALUES (?, ?, ?, ?)",
            (user["id"], safe_name[:255], str(stored_path.relative_to(BASE_DIR)), extracted),
        )
        db.commit()
        db.close()
        flash("Document uploaded and text extracted.", "success")
        return redirect(url_for("documents", id=cursor.lastrowid))
    rows = db.execute(
        "SELECT id, original_name, created_at FROM documents WHERE user_id = ? ORDER BY created_at DESC",
        (user["id"],),
    ).fetchall()
    document = None
    if selected:
        document = db.execute(
            "SELECT id, original_name, extracted_text, analysis FROM documents WHERE id = ? AND user_id = ?",
            (selected, user["id"]),
        ).fetchone()
        if document is None:
            db.close()
            abort(404)
    db.close()
    return render_template("documents.html", documents=rows, document=document)


@app.post("/documents/<int:document_id>/analyze")
def analyze_document(document_id):
    denied = login_required()
    if denied:
        return denied
    db = get_db()
    document = db.execute(
        "SELECT extracted_text FROM documents WHERE id = ? AND user_id = ?",
        (document_id, session["user_id"]),
    ).fetchone()
    if document is None:
        db.close()
        abort(404)
    try:
        analysis = analyze_legal_document(document["extracted_text"])
        db.execute("UPDATE documents SET analysis = ? WHERE id = ?", (analysis, document_id))
        db.commit()
        flash("Document analysis is ready.", "success")
    except Exception as error:
        detail = str(error)
        if GEMINI_API_KEY:
            detail = detail.replace(GEMINI_API_KEY, "[REDACTED]")
        logger.error("Gemini document analysis failed (%s): %s", type(error).__name__, detail)
        flash("NyayaAI could not connect to the AI service right now. Please try again later.", "error")
    db.close()
    return redirect(url_for("documents", id=document_id))


@app.route("/library")
def library():
    return render_template("library.html", topics=[
        ("Consumer Rights", "Understand common questions about purchases, warranties, and complaint processes."),
        ("Cyber Crime", "Learn general digital safety steps and how online incidents may be reported."),
        ("Property", "Explore general concepts around tenancy, ownership records, and property disputes."),
        ("Employment", "Review broad workplace topics such as pay, leave, contracts, and grievance processes."),
        ("Family Law", "Find introductory information about family matters and where to seek support."),
        ("Criminal Law", "Read general information about procedure, reporting, and seeking legal help."),
        ("Civil Law", "Explore common civil dispute concepts and possible resolution routes."),
        ("Digital Safety", "Practical steps for protecting accounts, evidence, and personal information."),
    ])


@app.route("/profile", methods=["GET", "POST"])
def profile():
    denied = login_required()
    if denied:
        return denied
    user = current_user()
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        if not username or len(username) > 40 or "@" not in email or len(email) > 254:
            flash("Enter a valid username and email address.", "error")
        else:
            db = get_db()
            duplicate = db.execute(
                "SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?",
                (username, email, user["id"]),
            ).fetchone()
            if duplicate:
                flash("That username or email is already in use.", "error")
            else:
                db.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", (username, email, user["id"]))
                db.commit()
                flash("Profile updated.", "success")
            db.close()
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)


@app.route("/documents/<int:document_id>/download")
def download_document(document_id):
    denied = login_required()
    if denied:
        return denied
    db = get_db()
    row = db.execute(
        "SELECT original_name, stored_name FROM documents WHERE id = ? AND user_id = ?",
        (document_id, session["user_id"]),
    ).fetchone()
    db.close()
    if row is None:
        abort(404)
    path = (BASE_DIR / row["stored_name"]).resolve()
    if UPLOAD_DIR.resolve() not in path.parents or not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, download_name=row["original_name"])


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, title="Page not found",
                           message="We could not find that page or item."), 404


@app.errorhandler(400)
def bad_request(_error):
    return render_template("error.html", code=400, title="Request could not be verified",
                           message="Refresh the page and try again."), 400


@app.errorhandler(413)
def upload_too_large(_error):
    return render_template("error.html", code=413, title="File is too large",
                           message="Choose a document smaller than 5 MB and try again."), 413


@app.errorhandler(500)
def server_error(error):
    logger.error("Application error: %s", type(error).__name__)
    return render_template("error.html", code=500, title="Something went wrong",
                           message="Please try again in a moment."), 500


if __name__ == "__main__":
    app.run(debug=False)
