import os
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database.db import (
    init_db,
    get_user_by_username, get_user_by_email, create_user, get_user_by_id, update_user,
    create_conversation, get_conversations_by_user, get_conversation_by_id,
    delete_conversation, add_message, get_messages_by_conversation,
    update_conversation_title, get_conversation_count,
    save_document, get_documents_by_user, get_document_by_id,
    delete_document, get_document_count
)
from services.ai_service import get_ai_response, analyze_document
from services.document_service import (
    allowed_file, save_uploaded_file, extract_text, cleanup_file, get_file_extension
)

app = Flask(__name__)
app.config.from_object(Config)

# ── Jinja2 filters ────────────────────────────────────────────────────────────

@app.template_filter('datetimeformat')
def datetimeformat(value, fmt='%B %d, %Y'):
    """Format a SQLite datetime string for display in templates."""
    if not value:
        return ''
    if isinstance(value, str):
        for pattern in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
            try:
                return datetime.strptime(value, pattern).strftime(fmt)
            except ValueError:
                continue
        return value
    if hasattr(value, 'strftime'):
        return value.strftime(fmt)
    return str(value)

init_db(app)

# ── Auth decorator ────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Legal Library data ────────────────────────────────────────────────────────

LEGAL_TOPICS = {
    'contracts': {
        'title': 'Contracts & Agreements',
        'icon': '📄',
        'description': 'Understand contracts, agreements, and what to do if one is breached.',
        'content': {
            'overview': 'The Indian Contract Act, 1872 governs contracts in India. A valid contract requires a lawful offer, acceptance, consideration (something of value exchanged), free consent, legal capacity of parties, and a lawful object. Both written and oral contracts can be legally binding, but written contracts are far easier to prove.',
            'common_types': [
                'Breach of contract — one party fails to fulfil their obligations',
                'Non-payment under agreements or purchase orders',
                'Fraud or misrepresentation in contracts',
                'Void and voidable agreements',
                'Employment and service contract disputes',
                'Rental and lease agreement disputes',
                'Sale of goods disputes',
                'Non-disclosure agreement (NDA) violations',
            ],
            'what_to_do': [
                'Always get agreements in writing — even for small matters',
                'Read every clause carefully before signing anything',
                'Keep copies of all signed contracts and related communications',
                'If a breach occurs, send a written legal notice first',
                'Approach civil court or use arbitration as specified in the contract',
                'Keep records of all payment proofs, emails, and communications',
            ],
            'note': 'Always have important contracts reviewed by a lawyer before signing. Verbal contracts can be legally valid but are very difficult to prove in court. For high-value agreements, always use a registered written contract.'
        }
    },
    'consumer_rights': {
        'title': 'Consumer Rights',
        'icon': '🛡️',
        'description': 'Understand your rights as a consumer under Indian law.',
        'content': {
            'overview': 'The Consumer Protection Act, 2019 protects the rights of consumers in India and provides effective mechanisms for redressal of grievances. Every consumer has the right to be protected against unfair trade practices, defective goods, and deficient services.',
            'common_types': [
                'Defective products or goods',
                'Deficient or poor services',
                'Unfair trade practices by businesses',
                'Misleading advertisements',
                'Overcharging or billing errors',
                'E-commerce disputes and online shopping issues',
                'Insurance claim rejections',
                'Bank and financial service complaints',
            ],
            'what_to_do': [
                'Keep all purchase receipts, invoices, and warranties',
                'First complain to the seller, company, or service provider in writing',
                'File a complaint on the National Consumer Helpline: 1800-11-4000',
                'File online complaint at consumerhelpline.gov.in',
                'Approach District Consumer Commission for disputes up to ₹1 crore',
                'State Consumer Commission handles disputes from ₹1 crore to ₹10 crore',
                'Collect all evidence: photos, receipts, emails, chat records',
            ],
            'note': 'Consumer courts provide an affordable and faster alternative to civil courts. In many cases, you can file a complaint yourself without a lawyer. The filing fees are very low. Time limit to file is generally 2 years from the cause of action.'
        }
    },
    'employment': {
        'title': 'Employment Law',
        'icon': '💼',
        'description': 'Know your rights as an employee under Indian labour laws.',
        'content': {
            'overview': 'Indian employment law covers wages, working conditions, termination, maternity benefits, and more. Key laws include the Industrial Disputes Act, 1947, Shops and Establishments Act, Payment of Wages Act, and the new Labour Codes. The applicable law depends on the type of employer and industry.',
            'common_types': [
                'Wrongful termination or illegal retrenchment',
                'Non-payment of salary, dues, or full and final settlement',
                'Workplace harassment under the POSH Act, 2013',
                'Denial of leave, maternity benefits, or statutory rights',
                'Provident Fund (PF) and ESI related disputes',
                'Contractual disputes and bond enforcement',
                'Discrimination at the workplace',
            ],
            'what_to_do': [
                'Keep copies of your offer letter, employment contract, and salary slips',
                'Raise complaints with HR formally in writing — keep copies',
                'Approach the Labour Commissioner or Labour Court for wage disputes',
                'File a POSH complaint with the Internal Complaints Committee (ICC)',
                'Contact EPFO (Employees\' Provident Fund Organisation) for PF issues',
                'Check the Shops and Establishments Act applicable to your state',
            ],
            'note': 'Labour laws differ for the organised and unorganised sectors. The applicable law depends on your employer\'s size, industry, and your employment type. It is strongly recommended to consult a labour law specialist for serious workplace disputes.'
        }
    },
    'cyber_crime': {
        'title': 'Cyber Crime',
        'icon': '🔐',
        'description': 'Learn about online fraud, cyberbullying, hacking, and digital crimes.',
        'content': {
            'overview': 'Cyber crimes are offences committed using computers, mobile devices, or the internet. In India, cyber crimes are primarily governed by the Information Technology Act, 2000 (IT Act) and the Bharatiya Nyaya Sanhita (BNS), 2023 which replaced IPC.',
            'common_types': [
                'Online fraud, phishing, and scam calls',
                'Identity theft and impersonation',
                'Cyberbullying, online harassment, and stalking',
                'Hacking and unauthorized account access',
                'Spreading fake, defamatory, or morphed content online',
                'Online financial fraud (UPI scams, banking fraud)',
                'Ransomware and data theft',
                'Child pornography and online exploitation',
            ],
            'what_to_do': [
                'Do NOT respond or transfer money to suspicious calls or messages',
                'File a cybercrime complaint at cybercrime.gov.in (official government portal)',
                'Call National Cybercrime Helpline: 1930',
                'Contact your bank immediately if financial fraud occurs — request transaction reversal',
                'Keep all evidence: screenshots, call recordings, transaction IDs',
                'File an FIR at the nearest police station or cybercrime cell',
                'Report to platform (WhatsApp, Instagram, etc.) for content removal',
            ],
            'note': 'Act quickly in cases of financial cyber fraud — report to your bank within hours. The IT Act, 2000 provides legal framework for cyber crimes with penalties varying based on the offence. Always consult a cyber law specialist for serious cases.'
        }
    },
    'property': {
        'title': 'Property Law',
        'icon': '🏠',
        'description': 'Learn about property rights, ownership, disputes, and registration.',
        'content': {
            'overview': 'Property law in India covers the transfer, ownership, registration, and disputes related to immovable property. Key laws include the Transfer of Property Act, 1882, Registration Act, 1908, and RERA (Real Estate Regulation and Development Act, 2016).',
            'common_types': [
                'Property boundary and encroachment disputes',
                'Title and ownership disputes',
                'Tenant-landlord disputes and eviction matters',
                'Property fraud, forgery of documents',
                'Inheritance and succession disputes',
                'Builder-buyer disputes (delays, quality, possession)',
                'Land acquisition disputes',
            ],
            'what_to_do': [
                'Always verify property documents before buying — check title, encumbrances',
                'Check for pending dues, mortgages, or liens at the sub-registrar office',
                'Mandatory registration of property sale deed at the sub-registrar office',
                'File complaints against builders on the RERA portal of your state',
                'Get legal opinion from a property lawyer before any property transaction',
                'Keep original documents safely — make certified copies',
                'Approach civil court or Revenue court depending on the nature of dispute',
            ],
            'note': 'Property disputes can be complex and time-consuming. Always get documents verified by a qualified property lawyer before making any transaction. For builder disputes, approach your State RERA authority.'
        }
    },
    'family_law': {
        'title': 'Family Law',
        'icon': '👨‍👩‍👧',
        'description': 'Understand marriage, divorce, child custody, and inheritance laws.',
        'content': {
            'overview': 'Family law in India is largely governed by personal laws based on religion — Hindu Marriage Act, 1955, Muslim Personal Law, Indian Christian Marriage Act. The Special Marriage Act, 1954 applies to all religions and inter-religion marriages. The Protection of Women from Domestic Violence Act, 2005 is an important protective law.',
            'common_types': [
                'Divorce and judicial separation',
                'Child custody and guardianship disputes',
                'Maintenance and alimony',
                'Domestic violence and abuse',
                'Dowry harassment',
                'Adoption and foster care',
                'Succession and inheritance disputes',
                'Property rights of women',
            ],
            'what_to_do': [
                'Seek mediation or counselling before approaching court for matrimonial disputes',
                'Document all instances of domestic violence with dates, photos, medical records',
                'Approach the Protection Officer under Domestic Violence Act for immediate help',
                'Contact National Women Helpline: 181 or Police: 112 for emergencies',
                'Get a family law specialist lawyer for matrimonial and custody disputes',
                'Approach Lok Adalat for faster resolution of settlement-possible matters',
                'Know that women have rights to matrimonial home even without ownership',
            ],
            'note': 'Family law matters are sensitive and personal laws vary by religion. It is strongly advised to consult a qualified family law advocate for your specific situation. For domestic violence emergencies, contact police (112) immediately.'
        }
    },
    'criminal_law': {
        'title': 'Criminal Law',
        'icon': '⚖️',
        'description': 'Understand FIRs, bail, rights of the accused, and criminal procedure.',
        'content': {
            'overview': 'Criminal law in India is governed by the Bharatiya Nyaya Sanhita (BNS), 2023 (which replaced IPC), Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 (which replaced CrPC), and the Bharatiya Sakshya Adhiniyam (BSA), 2023 (which replaced the Evidence Act). These laws define offences, procedures, and rights.',
            'common_types': [
                'Filing and responding to FIRs',
                'Bail applications (Regular bail, Anticipatory bail)',
                'Cognizable vs non-cognizable offences',
                'Rights of the arrested person',
                'Warrant and summons proceedings',
                'Appeals and revisions in criminal courts',
                'Compoundable offences (that can be settled between parties)',
            ],
            'what_to_do': [
                'If you are a victim: File FIR at the nearest police station immediately',
                'If police refuse to register FIR: approach SP/SSP or file a complaint before Magistrate',
                'If you are accused: exercise your right to remain silent and consult a lawyer immediately',
                'You have the right to know the grounds of arrest',
                'You must be produced before a Magistrate within 24 hours of arrest',
                'Apply for bail as soon as possible through a criminal lawyer',
                'Keep all evidence safe: witnesses, documents, CCTV footage',
            ],
            'note': 'Criminal matters are extremely serious. It is essential to consult a qualified criminal lawyer immediately if you are accused of any offence or if you are a victim of a serious crime. Do not make any statement without legal advice.'
        }
    },
    'general_terms': {
        'title': 'General Legal Terms',
        'icon': '📚',
        'description': 'Understand common legal terms used in courts and documents.',
        'content': {
            'overview': 'Legal language can be confusing. Understanding basic legal terms helps you navigate courts, legal documents, and understand your rights. Here are some commonly encountered legal terms explained in simple language.',
            'common_types': [
                'FIR (First Information Report) — The first complaint filed with police for a cognizable offence',
                'Bail — Temporary release of an arrested person on surety/security',
                'Affidavit — A written sworn statement of facts signed before a magistrate or notary',
                'Injunction — A court order stopping someone from doing something',
                'Caveat — A notice filed to ensure the other party is heard before any order is passed',
                'Power of Attorney (PoA) — Legal authority given to someone to act on your behalf',
                'Writ — A formal written court order (e.g., Habeas Corpus, Mandamus)',
                'Suo Motu — When a court takes action on its own, without a party filing a petition',
                'Contempt of Court — Disobeying or disrespecting a court\'s authority or orders',
                'Lok Adalat — People\'s Court — a forum for alternative dispute resolution',
            ],
            'what_to_do': [
                'Always ask your lawyer to explain legal terms in simple language',
                'Never sign a document you do not fully understand',
                'Free legal aid is available through the District Legal Services Authority (DLSA)',
                'National Legal Services Authority (NALSA) provides free legal aid to eligible persons',
                'Call NALSA Helpline: 15100 for free legal advice',
            ],
            'note': 'Every citizen has the right to free legal aid if they cannot afford a lawyer (under the Legal Services Authorities Act, 1987). Contact your nearest District Legal Services Authority (DLSA) for assistance.'
        }
    },
}

# ── Routes — Public ───────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')


@app.route('/landing')
def landing():
    return render_template('landing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        if get_user_by_username(username):
            flash('Username already taken. Please choose another.', 'error')
            return redirect(url_for('register'))

        if get_user_by_email(email):
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        create_user(username, email, password_hash)
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('login'))

        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ── Routes — Protected ────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conv_count = get_conversation_count(user_id)
    doc_count = get_document_count(user_id)
    recent_convs = get_conversations_by_user(user_id)[:5]
    recent_docs = get_documents_by_user(user_id)[:3]
    return render_template('dashboard.html',
                           conv_count=conv_count,
                           doc_count=doc_count,
                           recent_convs=recent_convs,
                           recent_docs=recent_docs)


@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', conversation_id=None, messages=[])


@app.route('/chat/<int:conv_id>')
@login_required
def chat_conversation(conv_id):
    user_id = session['user_id']
    conv = get_conversation_by_id(conv_id, user_id)
    if not conv:
        flash('Conversation not found.', 'error')
        return redirect(url_for('history'))
    messages = get_messages_by_conversation(conv_id, user_id)
    return render_template('chat.html', conversation_id=conv_id, messages=messages)


# ── API — Chat ────────────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid request.'}), 400

    message_text = (data.get('message') or '').strip()
    conversation_id = data.get('conversation_id')
    user_id = session['user_id']

    if not message_text:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    if len(message_text) > 4000:
        return jsonify({'error': 'Message is too long. Please keep it under 4000 characters.'}), 400

    # Get or create conversation
    if not conversation_id:
        title = message_text[:60] + ('…' if len(message_text) > 60 else '')
        conversation_id = create_conversation(user_id, title)
    else:
        conv = get_conversation_by_id(conversation_id, user_id)
        if not conv:
            return jsonify({'error': 'Conversation not found.'}), 404

    # Save user message
    add_message(conversation_id, 'user', message_text)

    # Build history for context (up to last 10 messages, excluding the one just added)
    all_msgs = get_messages_by_conversation(conversation_id, user_id)
    context_history = [dict(m) for m in all_msgs][:-1][-10:]

    # Get AI response
    response_text, error = get_ai_response(message_text, context_history)

    if error:
        return jsonify({'error': error}), 503

    # Save assistant message
    add_message(conversation_id, 'assistant', response_text)

    return jsonify({
        'response': response_text,
        'conversation_id': conversation_id
    })


@app.route('/api/conversations')
@login_required
def api_conversations():
    convs = get_conversations_by_user(session['user_id'])
    return jsonify({'conversations': [dict(c) for c in convs]})


# ── Routes — History ──────────────────────────────────────────────────────────

@app.route('/history')
@login_required
def history():
    convs = get_conversations_by_user(session['user_id'])
    return render_template('history.html', conversations=convs)


@app.route('/api/conversation/delete/<int:conv_id>', methods=['POST'])
@login_required
def delete_conv(conv_id):
    if delete_conversation(conv_id, session['user_id']):
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete conversation.'}), 400


# ── Routes — Documents ────────────────────────────────────────────────────────

@app.route('/documents')
@login_required
def documents():
    docs = get_documents_by_user(session['user_id'])
    return render_template('documents.html', documents=docs)


@app.route('/documents/upload', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('documents'))

    file = request.files['file']
    if not file or file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('documents'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Allowed: PDF, DOCX, TXT, MD.', 'error')
        return redirect(url_for('documents'))

    filepath = None
    try:
        filepath, filename = save_uploaded_file(file)
        original_name = file.filename
        file_ext = get_file_extension(filename)

        extracted_text, error = extract_text(filepath, filename)

        if error:
            flash(f'Could not extract text: {error}', 'error')
            return redirect(url_for('documents'))

        doc_id = save_document(
            user_id=session['user_id'],
            filename=filename,
            original_filename=original_name,
            file_type=file_ext,
            extracted_text=extracted_text
        )

        flash('Document uploaded and text extracted successfully.', 'success')
        return redirect(url_for('document_view', doc_id=doc_id))

    except Exception:
        flash('An error occurred while processing the file.', 'error')
        return redirect(url_for('documents'))
    finally:
        if filepath:
            cleanup_file(filepath)


@app.route('/document/<int:doc_id>')
@login_required
def document_view(doc_id):
    doc = get_document_by_id(doc_id, session['user_id'])
    if not doc:
        flash('Document not found.', 'error')
        return redirect(url_for('documents'))
    return render_template('document_view.html', doc=doc)


@app.route('/api/document/<int:doc_id>/analyze', methods=['POST'])
@login_required
def api_analyze_document(doc_id):
    doc = get_document_by_id(doc_id, session['user_id'])
    if not doc:
        return jsonify({'error': 'Document not found.'}), 404

    data = request.get_json(silent=True) or {}
    analysis_type = data.get('type', 'full')

    if not doc['extracted_text']:
        return jsonify({'error': 'No text available to analyze.'}), 400

    result, error = analyze_document(doc['extracted_text'], analysis_type)
    if error:
        return jsonify({'error': error}), 503

    if isinstance(result, dict):
        return jsonify({'result': result, 'type': 'full'})
    else:
        return jsonify({'result': result, 'type': analysis_type})


@app.route('/api/document/<int:doc_id>/delete', methods=['POST'])
@login_required
def api_delete_document(doc_id):
    if delete_document(doc_id, session['user_id']):
        return jsonify({'success': True})
    return jsonify({'error': 'Failed to delete document.'}), 400


# ── Routes — Legal Library ────────────────────────────────────────────────────

@app.route('/legal-library')
@login_required
def legal_library():
    return render_template('legal_library.html', topics=LEGAL_TOPICS, selected_topic=None)


@app.route('/legal-library/<topic>')
@login_required
def legal_topic(topic):
    if topic not in LEGAL_TOPICS:
        flash('Topic not found.', 'error')
        return redirect(url_for('legal_library'))
    return render_template('legal_library.html', topics=LEGAL_TOPICS, selected_topic=topic)


# ── Routes — Profile ──────────────────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not username or not email:
            flash('Username and email are required.', 'error')
        elif len(username) < 3:
            flash('Username must be at least 3 characters.', 'error')
        else:
            existing_u = get_user_by_username(username)
            if existing_u and existing_u['id'] != user['id']:
                flash('Username already taken.', 'error')
            else:
                existing_e = get_user_by_email(email)
                if existing_e and existing_e['id'] != user['id']:
                    flash('Email already registered.', 'error')
                else:
                    update_user(user['id'], username, email)
                    session['username'] = username
                    flash('Profile updated successfully.', 'success')
                    user = get_user_by_id(session['user_id'])

    conv_count = get_conversation_count(session['user_id'])
    doc_count = get_document_count(session['user_id'])
    return render_template('profile.html', user=user,
                           conv_count=conv_count, doc_count=doc_count)


# ── Error Handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(413)
def file_too_large(e):
    flash('File too large. Maximum upload size is 10MB.', 'error')
    return redirect(url_for('documents'))


@app.errorhandler(403)
def forbidden(e):
    return render_template('500.html', error="403 Forbidden — Access Denied"), 403


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', error="An internal server error occurred."), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
