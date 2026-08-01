# INGRES Virtual Assistant

An AI-Driven Chatbot built for the Integrated Groundwater Information Retrieval System (INGRES). This application features a robust RAG (Retrieval-Augmented Generation) pipeline, document management, and an analytics dashboard.

## 🚀 Live Demo
- **Frontend (Vercel):** [https://ingres-chatbot-git-main-shaliha123s-projects.vercel.app/](https://ingres-chatbot-git-main-shaliha123s-projects.vercel.app/)
- **Backend API (Render):** [https://ingres-chatbot-e8yh.onrender.com/api/v1](https://ingres-chatbot-e8yh.onrender.com/api/v1)

---

## 🛠 Tech Stack
- **Frontend:** Vanilla HTML5, CSS3, JavaScript
- **Backend:** Python, FastAPI
- **Database:** MongoDB
- **AI / LLM:** Google Gemini API
- **Deployment:** Vercel (Frontend) & Render (Backend)

---

## 📂 Project Structure

`
.
├── backend/
│   ├── app/                # FastAPI application code
│   ├── scripts/            # Database management and utility scripts
│   ├── tests/              # E2E tests, RAG pipeline tests, and Audits
│   └── requirements.txt    # Python dependencies
├── frontend/               # Static UI files (HTML, JS, CSS)
├── reports/                # Generated audit and verification markdown reports
├── render.yaml             # Render deployment blueprint
└── README.md               # You are here!
`

---

## 💻 Local Development Setup

### 1. Clone the repository
\\\ash
git clone https://github.com/Shaliha123/INGRES-Chatbot.git
cd INGRES-Chatbot
\\\

### 2. Backend Setup
Make sure you have Python 3.10+ installed.
\\\ash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
\\\

Create a .env file in the ackend/ directory and populate your secrets:
\\\env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=ingres_db
GEMINI_API_KEY=your_gemini_key_here
FIREBASE_PROJECT_ID=your_firebase_id_here
\\\

Start the local server:
\\\ash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
\\\

### 3. Frontend Setup
Since the frontend uses vanilla HTML/JS, no build step is required! 
You can serve the rontend/ directory using any local static file server (e.g., Live Server extension in VSCode, or Python's http.server):
\\\ash
cd frontend
python -m http.server 3000
\\\
Open http://localhost:3000 in your browser.

---

## 🔒 Security
- Production CORS is restricted strictly to the Vercel frontend URL.
- Environment variables containing API Keys are managed securely through Render and are excluded from version control.
