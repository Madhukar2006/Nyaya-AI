# NyayaAI — AI-Powered Legal Assistance & Document Intelligence System

> **NyayaAI provides general legal information and is not a substitute for professional legal advice.**

---

## Problem Statement

Access to legal knowledge in India is often limited by cost, language barriers, and lack of awareness. NyayaAI bridges this gap by providing a conversational AI interface that explains legal concepts, helps users understand their rights, and guides them through common legal situations — in English, Hindi, and Hinglish.

---

## Features

- **AI Legal Chatbot** — Conversational Q&A powered by OpenAI GPT
- **Multi-language Support** — English, Hindi, and Hinglish
- **Chat History** — All conversations saved per user, viewable and deleteable
- **Document Intelligence** — Upload PDF legal documents for AI-powered analysis
- **Legal Library** — Browse common legal topics with practical guidance
- **User Authentication** — Register, login, logout with secure password hashing
- **Session-based Auth** — Protected routes, per-user data isolation
- **Responsive UI** — Clean chatbot interface with suggestion buttons

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.x, Flask 3.0 |
| AI | OpenAI GPT-4o-mini (via OpenAI Python SDK) |
| Database | SQLite (via Python `sqlite3`) |
| Auth | Flask sessions + Werkzeug password hashing |
| PDF Parsing | PyPDF2 |
| Frontend | HTML5, Vanilla CSS, Vanilla JavaScript |
| Config | python-dotenv |

---

## Project Architecture

```
NyayaAI/
├── app.py                  # Main Flask application, routes, Jinja2 filters
├── config.py               # Configuration class (loads from .env)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── .gitignore              # Git exclusions
├── README.md               # This file
├── database/
│   ├── db.py               # SQLite helper functions (CRUD)
│   └── schema.sql          # Table definitions
├── services/
│   ├── ai_service.py       # OpenAI API integration
│   └── document_service.py # PDF upload, text extraction
├── templates/
│   ├── layout.html         # Base template with navbar and flash messages
│   ├── chat.html           # Main chat interface
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── history.html        # Conversation history list
│   ├── documents.html      # PDF upload and analysis results
│   ├── legal_library.html  # Legal topic browser
│   ├── profile.html        # User profile editor
│   ├── 404.html            # 404 error page
│   └── 500.html            # 500 error page
└── static/
    ├── css/style.css       # Application stylesheet
    └── js/main.js          # Chat UI JavaScript
```

---

## Database Schema

```sql
-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversations (one per chat session, belongs to user)
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Messages (individual chat messages)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);
```

---

## OpenAI API Integration

NyayaAI uses the **OpenAI Python SDK** with `gpt-4o-mini`:

```python
from openai import OpenAI
from config import Config

client = OpenAI(api_key=Config.OPENAI_API_KEY)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ],
    max_tokens=1500
)

answer = response.choices[0].message.content
```

The API key is **never** exposed in HTML, JavaScript, or browser requests — all calls are made server-side.

---

## Installation

### Prerequisites

- Python 3.10+
- An OpenAI API key from [platform.openai.com](https://platform.openai.com)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/madhukar2006/NyayaAI.git
cd NyayaAI

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your actual Groq API key

# 5. Run the application
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
SECRET_KEY=your-random-secret-key-here
```

> **Never commit your `.env` file.** It is excluded by `.gitignore`.

---

## Usage

1. **Register** — Create an account at `/register`
2. **Login** — Sign in at `/login`
3. **Chat** — Ask legal questions in plain language at `/chat`
4. **History** — View and delete past conversations at `/history`
5. **Documents** — Upload a PDF legal document for AI analysis at `/documents`
6. **Legal Library** — Browse topic guides at `/legal-library`
7. **Profile** — Update your username or email at `/profile`
8. **Logout** — End your session at `/logout`

---

## Security

- Passwords stored as bcrypt hashes (via Werkzeug)
- Flask session cookies (server-side session)
- All private routes protected with `@login_required`
- Conversation ownership verified on every request (users cannot access other users' data)
- OpenAI API key loaded from environment — never exposed in frontend
- Uploaded files sanitized with `werkzeug.utils.secure_filename`
- File size limited to 5MB
- PDF files deleted from server immediately after text extraction
- `.env` excluded from Git via `.gitignore`
- Internal errors never exposed to the user

---

## Legal Disclaimer

NyayaAI provides **general legal information only**. It is **not** a law firm and does not provide legal advice. No attorney-client relationship is created by using NyayaAI.

For specific legal matters, always consult a qualified legal professional.

---

## AI Assistance Disclosure

This application uses OpenAI's language model (GPT-4o-mini) to generate responses. AI responses may contain inaccuracies. NyayaAI will never:
- Invent laws, court cases, or legal citations
- Guarantee legal outcomes
- Claim to be a licensed lawyer

---

## Future Scope

- [ ] Support for more document types (DOCX, images via OCR)
- [ ] Voice input support
- [ ] Case tracking and reminders
- [ ] Regional language support (Tamil, Telugu, Bengali, etc.)
- [ ] Integration with official government legal portals
- [ ] Lawyer directory / referral feature
- [ ] Export conversation as PDF
