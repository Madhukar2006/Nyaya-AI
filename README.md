# ⚖️ NyayaAI

> **AI-powered legal information and document assistant.**

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-blue?logo=sqlite)](https://www.sqlite.org/)
[![Gemini](https://img.shields.io/badge/Google-Gemini-orange?logo=google)](https://ai.google.dev/)

**NyayaAI** is a web-based AI assistant designed to help users understand general legal information, ask questions, and review uploaded documents through an easy-to-use conversational interface.

> ⚠️ **Disclaimer:** NyayaAI provides general legal information for educational purposes and does not replace professional legal advice.

---

## ✨ Features

- 🤖 AI-powered legal information assistant
- 💬 Interactive conversations
- 🌐 English, Hindi & Hinglish support
- 🔐 User authentication
- 💾 Private chat history
- 📄 PDF, DOCX, TXT & Markdown document support
- 🔍 AI-assisted document review
- 📚 Legal information library
- 👤 User profile management
- 📱 Responsive web interface

---

## 🖼️ Screenshots

### 🏠 Dashboard

> Add dashboard screenshot here.

![Dashboard](screenshots/dashboard.png)

### 💬 AI Chat

> Add chat screenshot here.

![Chat](screenshots/chat.png)

### 📄 Document Review

> Add document review screenshot here.

![Document Review](screenshots/document-review.png)

---

## 🧠 How It Works

```text
User
  │
  ▼
NyayaAI Web Interface
  │
  ├── AI Chat ──────────────┐
  │                         │
  └── Document Upload       │
            │               │
            ▼               ▼
      Text Extraction → Gemini AI
                            │
                            ▼
                       AI Response
                            │
                            ▼
                         User
```

---

## 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| Python | Backend |
| Flask | Web Framework |
| Google Gemini | AI |
| SQLite | Database |
| HTML | Structure |
| CSS | Styling |
| JavaScript | Frontend functionality |
| pypdf | PDF processing |
| python-docx | DOCX processing |

---

## 📁 Project Structure

```text
NyayaAI/
│
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .env.example
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── chat.html
│   └── profile.html
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── database/
│
└── uploads/
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Madhukar2006/NyayaAI.git
cd NyayaAI
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate environment

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key
SECRET_KEY=your_secret_key
```

### 6. Run the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 🌍 Supported Languages

NyayaAI currently supports:

- 🇬🇧 English
- 🇮🇳 Hindi
- 🗣️ Hinglish

---

## 📄 Document Support

NyayaAI supports text extraction from:

```text
PDF
DOCX
TXT
MD
```

Uploaded documents can be processed and used for AI-assisted explanations and review.

---

## 🗺️ Roadmap

- [x] AI Chat
- [x] User Authentication
- [x] Chat History
- [x] Document Upload
- [x] PDF Support
- [x] DOCX Support
- [x] Hindi Support
- [x] Hinglish Support
- [ ] Better legal source citations
- [ ] Advanced document analysis
- [ ] Conversation export
- [ ] Document history
- [ ] More Indian languages
- [ ] Automated testing
- [ ] Production deployment

---

## 🤝 Contributing

Contributions are welcome!

```text
Fork → Create Branch → Make Changes → Pull Request
```

You can contribute by:

- 🐛 Fixing bugs
- ✨ Adding features
- 🎨 Improving UI
- 📚 Improving documentation
- 🌐 Adding language support
- 🧪 Adding tests

---

## ⚠️ Disclaimer

NyayaAI is an educational project intended to provide general legal information.

It does **not** provide professional legal advice and does not create an attorney-client relationship.

For specific legal matters, consult a qualified legal professional.

---

## 👨‍💻 Author

### Madhukar Pal

**GitHub:** [@Madhukar2006](https://github.com/Madhukar2006)

**Portfolio:** [madhukar2006.github.io/Portfolio](https://madhukar2006.github.io/Portfolio/)

---

## ⭐ Support

If you find **NyayaAI** useful:

⭐ Star the repository  
🍴 Fork the repository  
🐛 Report bugs  
💡 Suggest features

---

<p align="center">
  Made with ❤️ by <b>Madhukar Pal</b>
</p>
