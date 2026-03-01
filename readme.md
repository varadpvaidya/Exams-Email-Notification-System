# 🚀 VARAD AI – Automated Daily Exam Update Engine

**VARAD AI** is an advanced academic automation system that:

- 📥 Fetches structured exam data from Google Apps Script  
- 🤖 Uses LLM (via Groq API) to generate strict-format academic JSON  
- 🛡 Validates output against rigid structural rules  
- 📧 Builds a premium HTML email  
- 📤 Sends the final email via Apps Script  

This project ensures **100% structured, validated, production-safe academic email updates.**

---

## 🧠 System Architecture

Google Sheets  
      ↓  
Google Apps Script (Web App)  
      ↓  
Python Backend  
      ↓  
Groq LLM (openai/gpt-oss-120b)  
      ↓  
Strict JSON Validation  
      ↓  
HTML Email Builder  
      ↓  
Apps Script Mail Sender  

---

# 📂 Project Structure

.
├── main.py  
├── mailing.py  
├── elements.py  
├── emailtemplate.html  
├── requirements.txt  
├── .env  

---

# 📄 File Overview

---

## 🔹 main.py

Core orchestration engine.

Responsibilities:
- Loads environment variables  
- Fetches exam data from Apps Script (`getdata`)  
- Builds strict AI prompt  
- Calls Groq LLM  
- Validates JSON output:
  - Exact key order  
  - Date format  
  - Allowed HTML tags  
  - Execution task limits  
- Retries up to 3 times if invalid  
- Passes valid JSON to email builder  
- Triggers send email  

---

## 🔹 mailing.py

Handles HTML generation and email sending.

Features:
- Emoji → Twemoji image conversion (email-safe) (You can have other emoji platform as well)  
- Dynamic section removal if empty  
- Execution Task block rendering  
- Upcoming Exam block rendering  
- Application Update block rendering  
- Sends final HTML using Apps Script `sendmail`  

---

## 🔹 elements.py

Contains reusable HTML fragments for:

- Execution Task row  
- Upcoming Exam card  
- Application Deadline row  
- Application Opening row  

These fragments are injected into the master template.

---

## 🔹 emailtemplate.html

Premium email-safe HTML layout.

Includes:
- Header section  
- Quick Summary card  
- Execution Tasks table  
- Upcoming Exams section  
- Application Updates section  
- Footer branding  

Fully responsive and Outlook-safe.

---

## 🔹 requirements.txt

requests>=2.31.0  
python-dotenv>=1.0.0  
groq>=0.9.0  

---

# 🔐 Environment Variables (.env)

Create a `.env` file in root:

GROQ_API_KEY=your_groq_api_key  
SECRET_KEY=your_secret_key  
WEBAPP_URL=https://script.google.com/macros/s/XXXXX/exec  

Important:
- `SECRET_KEY` must match Apps Script Properties.  
- Used for both `getdata` and `sendmail`.

---

# 🧪 JSON Validation Rules

The system enforces:

- Exact key order  
- Strict date format: DD-MMM-YYYY  
- Allowed HTML tags: <a>, <strong> only  
- Max 6 execution tasks  
- Application type must be:
  - "Deadline"  
  - "Opening"  
- Proper anchor validation  

If validation fails → automatic retry (max 3 attempts).

---

# ⚙️ Installation

### 1️⃣ Clone repository

```https://github.com/varadpvaidya/Exams-Email-Notification-System.git```

```cd Exams-Email-Notification-System```

### 2️⃣ Create virtual environment (recommended)

```python -m venv venv```
```source venv/bin/activate  # Mac/Linux  ```
```venv\Scripts\activate     # Windows  ```

### 3️⃣ Install dependencies

```pip install -r requirements.txt ```

---

# ▶️ Run the Project

```python main.py  ```

---

# 🔄 How It Works (Execution Flow)

1. Fetch exam data from Apps Script  
2. Construct strict LLM prompt  
3. Generate structured JSON  
4. Validate response  
5. Build email HTML  
6. Send email via Apps Script  

---

# 🎯 Design Principles

- Zero malformed JSON tolerance  
- Email-client safe HTML  
- Strict deterministic LLM usage (temperature=0)  
- Retry-safe  
- Modular structure  
- Production-ready validation  

---

# 🛡 Security

- Secrets stored in `.env`  
- API key never hardcoded  
- Apps Script protected via `SECRET_KEY`  
- Strict HTML tag filtering  

---

# 🧩 Customization

You can:

- Modify email design → `emailtemplate.html`  
- Change UI components → `elements.py`  
- Adjust validation rules → `main.py`  
- Upgrade model → change in Groq call  

---

# 🌍 Open Source & Contributions

This project is **completely free to use, edit, and modify**.

You are welcome to:
- Improve the architecture  
- Suggest performance optimizations  
- Enhance validation logic  
- Improve email UI/UX  
- Add new automation features  

Pull requests, suggestions, and improvements are always welcome 🙌  

---


