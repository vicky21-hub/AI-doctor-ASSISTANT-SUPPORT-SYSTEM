# 🩺 AI Doctor Assistant Support System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://ai-doctor-assistant-support-system.onrender.com)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://ai-doctor-assistant-support-system.onrender.com)
[![React 19](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Flask](https://img.shields.io/badge/Backend-Flask%20%2B%20Python%203.11-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

> **Live Deployment:** [https://ai-doctor-assistant-support-system.onrender.com](https://ai-doctor-assistant-support-system.onrender.com)

A comprehensive, production-grade AI Healthcare Assistant that conducts structured medical consultations, performs OCR-based medical report analysis, predicts conditions with clinical decision trees, and delivers triaged health guidance in English, Telugu, and Hindi.

---

## 🌟 Key Features

### 1. 🤖 Dynamic Clinical Consultation Engine
- **Conversational State Machine**: Gathers symptoms, severity, location, duration, and patient profile (age, gender, existing conditions) in a natural clinical sequence.
- **Smart Natural Language Extraction**: Parses compound descriptions (e.g., *"burning sensation while urinating since 2 days with mild lower abdominal pain"*), extracts discrete medical facts, negations, triggers, and numbers.
- **Adaptive Question Trees**: Automatically detects the clinical category (`urinary`, `vomiting`, `respiratory`, `chest_pain`, etc.) and asks only missing, relevant follow-up questions.
- **Strict Input Validation**: Validates yes/no answers, numerical counts, durations, age, and gender, prompting for clarification without saving invalid answers.
- **Emergency Detection & Escalation**: Monitors for red-flag symptoms (severe chest pain, shortness of breath, blood in vomit/stool) and triggers immediate emergency recommendations.

### 2. 📄 Medical Report OCR & Lab Analysis
- **Automated Text Extraction**: Extracts text from lab test images and PDF reports using **Tesseract OCR** and **pdfplumber**.
- **Biomarker Recognition**: Interprets vital metrics (blood glucose, cholesterol, liver panels, CBC) and provides plain-language summaries with risk categorization.

### 3. 🧠 Disease Prediction & Symptom Matching
- **Machine Learning Matcher**: Combines **scikit-learn** and **rapidfuzz** string algorithms to match over 41 human conditions and 20 veterinary conditions.
- **Differential Assessment**: Returns primary condition hypotheses, confidence scores, and self-care recommendations.

### 4. 🌐 Multilingual Accessibility
- Full language support for **English**, **Telugu (తెలుగు)**, and **Hindi (हिन्दी)** with instant UI language toggling.

### 5. 🎨 Modern Glassmorphism UI
- **Light & Dark Mode**: Persistent theme switching with glassmorphism styling and neon accent glowing.
- **Framer Motion**: Smooth page transitions, animated consultation progress bars, and responsive interactive elements.

---

## 🏗️ System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        User Browser (Desktop / Mobile)                 │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTPS
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Single Docker Container (Port 5000 / $PORT)           │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                     Gunicorn WSGI Server                       │   │
│   └───────────────┬────────────────────────────────┬───────────────┘   │
│                   │                                │                   │
│                   ▼                                ▼                   │
│   ┌──────────────────────────────┐ ┌───────────────────────────────┐   │
│   │  Flask Frontend Static Host  │ │       Flask REST API (/api)   │   │
│   │  Serves compiled React SPA   │ │  - Rate Limiter (Flask-Limiter│   │
│   │  (/, /chat, /dashboard, etc.)│ │  - CORS Guard                 │   │
│   └──────────────────────────────┘ └───────────────┬───────────────┘   │
│                                                    │                   │
│         ┌───────────────────┬──────────────────────┴─────┬────────────┐│
│         ▼                   ▼                            ▼            ▼│
│   ┌────────────┐     ┌──────────────┐             ┌────────────┐ ┌────┐│
│   │Consultation│     │  OCR Engine  │             │ ML Symptom │ │Auth││
│   │Engine (NLP)│     │(Tesseract/PDF│             │  Matcher   │ │JWT ││
│   └─────┬──────┘     └──────┬───────┘             └─────┬──────┘ └─┬──┘│
│         │                   │                           │          │   │
│         └───────────────────┴─────────────┬─────────────┴──────────┘   │
│                                           ▼                            │
│                              SQLite Database & Uploads                 │
│                              (health_assistant.db)                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend Framework** | React 19, TypeScript, Vite 8 |
| **Styling & Design** | Tailwind CSS v4, PostCSS, Lucide Icons, Glassmorphism UI |
| **Animation & UI** | Framer Motion, React Router DOM v7 |
| **Internationalization** | i18next, react-i18next (English, Telugu, Hindi) |
| **Backend Framework** | Python 3.11, Flask 3.0, Werkzeug |
| **WSGI Server** | Gunicorn 22 (Multi-worker, gthread) |
| **Machine Learning & NLP** | scikit-learn, rapidfuzz, regex extractors |
| **OCR & Document Parsing** | Tesseract OCR 5, pytesseract, pdfplumber, OpenCV (headless), Pillow |
| **Security & Auth** | PyJWT, Flask-Limiter, PBKDF2 Password Hashing |
| **Database** | SQLite 3 |
| **Containerization** | Docker (Multi-stage build: `node:20-slim` + `python:3.11-slim`) |
| **Cloud Hosting** | Render (Docker Web Service) |

---

## 📸 Screenshots

| Landing Page | AI Doctor Chat Consultation |
| :---: | :---: |
| ![Landing Page](https://raw.githubusercontent.com/vicky21-hub/AI-doctor-ASSISTANT-SUPPORT-SYSTEM/master/public/favicon.svg) <br> *Landing Page with Quick Checkup* | ![Consultation](https://raw.githubusercontent.com/vicky21-hub/AI-doctor-ASSISTANT-SUPPORT-SYSTEM/master/public/icons.svg) <br> *Live Doctor-Patient Consultation* |

*(Screenshots can also be viewed live at [ai-doctor-assistant-support-system.onrender.com](https://ai-doctor-assistant-support-system.onrender.com))*

---

## 🔌 API Overview

All backend routes are prefixed under `/api`:

| Method | Endpoint | Description | Rate Limit |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Health check probe | Default |
| `GET` | `/api/health/ocr` | Diagnostic status for Tesseract & pytesseract | Default |
| `POST` | `/api/chat` | Main AI consultation engine turn | 30 / min |
| `POST` | `/api/upload` | Upload lab reports / medical images | 10 / min |
| `POST` | `/api/analyze` | Run OCR & clinical analysis on uploaded file | Default |
| `POST` | `/api/predict` | Fast symptom disease prediction | Default |
| `POST` | `/api/vet/chat` | Veterinary pet health consultation | Default |
| `GET` | `/api/history` | Retrieve user consultation history | Default |
| `POST` | `/api/auth/signup` | Register new user account | 5 / min |
| `POST` | `/api/auth/login` | Authenticate user & issue JWT | 10 / min |
| `GET` | `/api/auth/profile`| Get authenticated user profile | Default |

---

## 💻 Local Setup & Development

### Prerequisites
- **Node.js** (v18 or v20+) & **npm**
- **Python** 3.10+
- **Tesseract-OCR** ([Install Guide](https://github.com/tesseract-ocr/tesseract))

### Option A: Running with Docker (Recommended)

Run the entire full-stack application with a single command:

```bash
# 1. Clone the repository
git clone https://github.com/vicky21-hub/AI-doctor-ASSISTANT-SUPPORT-SYSTEM.git
cd AI-doctor-ASSISTANT-SUPPORT-SYSTEM

# 2. Build and run using Docker Compose
docker compose up --build
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

### Option B: Running Manually

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the Flask backend
python app.py
```
Backend will start on `http://localhost:5000`.

#### 2. Frontend Setup
Open a separate terminal in the root directory:
```bash
# Install frontend dependencies
npm install

# Start Vite development server
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## 🚀 Cloud Deployment

The repository includes a ready-to-use **[Dockerfile](Dockerfile)** and **[render.yaml](render.yaml)** for 1-click cloud deployment.

### Deploying to Render:
1. Fork or clone this repository to your GitHub account.
2. Sign in to [Render](https://render.com).
3. Click **New +** → **Web Service** → Select your repository.
4. Render automatically detects the **Dockerfile**:
   - **Environment**: Docker
   - **Plan**: Free ($0/month)
5. Click **Create Web Service**. Render builds the React frontend, packages Tesseract OCR, and starts Gunicorn automatically.

---

## ⚠️ Medical Disclaimer

> **IMPORTANT**: This application is developed for **educational, triage assistance, and demonstration purposes only**. It does NOT provide formal medical diagnoses or replace consultations with licensed healthcare professionals. In the event of a medical emergency, immediately contact your local emergency services (e.g., 911, 112, or 108).

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
