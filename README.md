# 🌊 INGRES Virtual Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248.svg?logo=mongodb)](https://www.mongodb.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An advanced, AI-driven conversational agent engineered specifically for the **Integrated Groundwater Information Retrieval System (INGRES)**. It leverages a cutting-edge Retrieval-Augmented Generation (RAG) pipeline to provide accurate, context-aware answers regarding groundwater levels, rainfall forecasts, water quality parameters, and CGWB reports.

---

## 📑 Table of Contents
1. [Live Demo](#-live-demo)
2. [Key Features](#-key-features)
3. [Architecture Overview](#-architecture-overview)
4. [Tech Stack](#-tech-stack)
5. [Prerequisites](#-prerequisites)
6. [Environment Variables](#-environment-variables)
7. [Local Installation](#-local-installation)
8. [Deployment Guide](#-deployment-guide)
9. [Project Structure](#-project-structure)

---

## 🚀 Live Demo

Experience the live production application here:

- **Frontend Application (Vercel):** [https://ingres-chatbot-git-main-shaliha123s-projects.vercel.app/](https://ingres-chatbot-git-main-shaliha123s-projects.vercel.app/)
- **Backend API Server (Render):** [https://ingres-chatbot-e8yh.onrender.com/api/v1/health](https://ingres-chatbot-e8yh.onrender.com/api/v1/health)

---

## ✨ Key Features

- **🧠 Intelligent RAG Chatbot:** Combines Google Gemini LLM with vector-search retrieval for hyper-accurate, document-backed responses.
- **📊 Real-time Analytics Dashboard:** Visualize system usage, query intent breakdown, user engagement, and LLM performance.
- **📁 Document Management:** Admins can upload PDFs and TXT files. The system automatically chunks, embeds, and indexes them for the RAG pipeline.
- **🔐 Secure Authentication:** Full JWT-based user authentication and role-based access control (Admin vs User).
- **📝 Conversation History:** Secure storage of all chat transcripts, allowing users to revisit past queries.
- **📱 Responsive UI:** A modern, sleek, enterprise-grade vanilla web interface tailored for hydrogeological data.

---

## 🏗 Architecture Overview

\\mermaid
graph TD;
    Client[Frontend: HTML/JS] -->|REST API| FastAPI[Backend: FastAPI]
    FastAPI -->|JWT/Auth| Middleware[Security Layer]
    Middleware --> Routers[API Routers]
    Routers --> RAG[RAG Pipeline Engine]
    RAG -->|Vector Search| MongoDB[(MongoDB Atlas)]
    RAG -->|Prompt Gen| LLM[Google Gemini API]
    Routers -->|Manage| Docs[Document Management]
    Docs -->|Upload/Chunk| MongoDB
\
---

## 🛠 Tech Stack

### Frontend
- **Core:** HTML5, CSS3, Vanilla JavaScript (ES6+)
- **Map Integration:** Leaflet.js (for geospatial data)
- **Charting:** Chart.js (for analytics)
- **Icons:** FontAwesome / Heroicons

### Backend
- **Framework:** Python 3.10+, FastAPI, Uvicorn
- **AI/LLM:** Google Gemini API (via google-generativeai)
- **Database:** MongoDB (Motor Async Driver)
- **Security:** PyJWT, Passlib (Bcrypt)

---

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.10** or higher
- **Git**
- **MongoDB** (Local instance running on port 27017, or a MongoDB Atlas URI)
- A **Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/))

---

## 🔐 Environment Variables

Create a \.env\ file inside the \ackend/\ directory. Use the following template:

\\env
# Database Settings
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=ingres_db

# AI & LLM Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Security Settings
SECRET_KEY=generate_a_secure_random_string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Optional Firebase Config (if used)
FIREBASE_PROJECT_ID=your_project_id
\
---

## 💻 Local Installation

### 1. Clone the Repository
\\ash
git clone https://github.com/Shaliha123/INGRES-Chatbot.git
cd INGRES-Chatbot
\
### 2. Backend Setup
\\ash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scriptsctivate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
\
### 3. Start the Backend Server
\\ash
# Run the FastAPI server via Uvicorn
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
\The API will be available at \http://127.0.0.1:8000\. You can view the interactive API documentation at \http://127.0.0.1:8000/docs\.

### 4. Start the Frontend
Open a new terminal window. Since the frontend is static, you just need a simple HTTP server:
\\ash
cd frontend
python -m http.server 3000
\Open your browser and navigate to \http://localhost:3000\.

---

## 🌍 Deployment Guide

### Deploying the Backend (Render)
1. Go to [Render](https://render.com/) and create a new **Web Service**.
2. Connect your GitHub repository.
3. Set the Root Directory to \ackend\.
4. Build Command: \pip install -r requirements.txt5. Start Command: \gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:\
6. Add your \.env\ variables in the Render Environment tab.

### Deploying the Frontend (Vercel)
1. Go to [Vercel](https://vercel.com/) and click **Add New Project**.
2. Import your GitHub repository.
3. Set the **Root Directory** to \rontend\.
4. Click Deploy. Vercel will automatically serve your static files!

---

## 📂 Detailed Project Structure

\\	ext
INGRES-Chatbot/
├── backend/
│   ├── app/
│   │   ├── middleware/      # Auth & Logging interceptors
│   │   ├── routers/         # API Endpoints (auth, chat, admin, docs)
│   │   ├── schemas/         # Pydantic data validation models
│   │   ├── services/        # Core business logic (RAG, LLM, Prompts)
│   │   ├── config.py        # Environment variables loader
│   │   ├── database.py      # MongoDB connection manager
│   │   └── main.py          # FastAPI application entry point
│   ├── scripts/             # DB migration & utility scripts
│   ├── tests/               # E2E and Unit test suites
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── css/                 # Stylesheets & Theme
│   ├── js/                  # API client & UI logic
│   ├── images/              # Assets
│   └── *.html               # View templates (dashboard, chat, admin)
├── render.yaml              # Render IaC configuration
└── README.md                # Project documentation
\
---

*Built with ❤️ for the Integrated Groundwater Information Retrieval System.*
