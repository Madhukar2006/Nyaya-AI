# NyayaAI

AI-powered legal information assistant for exploring general information about Indian law.

> **Disclaimer:** NyayaAI provides general legal information for educational and informational purposes only. It is not a substitute for professional legal advice.

## Features

- AI legal assistant for general questions about Indian law
- English, Hindi, and Hinglish support
- Conversation history with user-specific chat storage
- Legal document analysis
- Support for PDF, DOCX, TXT, and Markdown files
- Multiple document analysis modes
- Legal library with common legal topics
- User registration, login, logout, and profile management
- Responsive web interface
- Secure file handling and environment-based API configuration

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| AI | Groq API |
| Database | SQLite |
| Frontend | HTML5, CSS3, JavaScript |
| Authentication | Flask Sessions, Werkzeug |
| PDF Processing | pypdf |
| DOCX Processing | python-docx |
| Configuration | python-dotenv |

## Project Structure

```text
Nyaya-AI/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
│
├── database/
│   ├── db.py
│   └── schema.sql
│
├── services/
│   ├── ai_service.py
│   └── document_service.py
│
├── templates/
│   ├── landing.html
│   ├── layout.html
│   ├── dashboard.html
│   ├── chat.html
│   ├── history.html
│   ├── documents.html
│   ├── document_view.html
│   ├── legal_library.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── 404.html
│   └── 500.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- A Groq API key

### Clone the repository

```bash
git clone https://github.com/Madhukar2006/Nyaya-AI.git
cd Nyaya-AI
```

### Create a virtual environment

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file using `.env.example` as a reference:

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_random_flask_secret_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

Keep your API keys private and never commit the `.env` file.

### Run the application

```bash
python app.py
```

Open the application at:

```text
http://127.0.0.1:5000
```

## How It Works

1. Users create an account and sign in.
2. Legal questions are submitted through the chat interface.
3. The Flask backend sends the request to the configured Groq model.
4. AI responses are returned to the user and conversations are stored in SQLite.
5. Users can upload supported documents for text extraction and AI analysis.
6. Uploaded files are cleaned up after processing.

## Document Support

NyayaAI currently supports:

| Format | Description |
|---|---|
| PDF | Extract and analyze selectable text |
| DOCX | Extract and analyze Word document text |
| TXT | Analyze plain text files |
| MD | Analyze Markdown files |

Scanned PDFs without selectable text may not be processed successfully.

## Security

The application includes:

- Password hashing using Werkzeug
- Session-based authentication
- Protected private routes
- User-level access control for conversations and documents
- Secure filename handling
- Configurable upload size limits
- API credentials stored in environment variables
- Temporary uploaded-file cleanup

## Legal Notice

NyayaAI is an educational and informational project. AI-generated responses may contain incomplete or inaccurate information and should not be considered legal advice.

For important legal matters, users should verify information with reliable official sources and consult a qualified legal professional.

## Future Improvements

- OCR support for scanned documents
- Additional document formats
- Voice input
- More regional Indian languages
- Integration with official legal and government resources
- Conversation export
- Case tracking and reminders

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Author

**Madhukar Pal**

GitHub: [@Madhukar2006](https://github.com/Madhukar2006)

---

Built as an AI and web development project to make general legal information easier to understand and explore.
