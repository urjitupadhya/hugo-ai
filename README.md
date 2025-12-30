# 🏭 Hugo AI: Intelligent Procurement Assistant

**Hugo AI** is a cutting-edge Supply Chain Operations agent designed to help procurement teams monitor inventory, detect risks, and chat with their data using Generative AI.

![Hugo AI](https://img.shields.io/badge/AI-Gemini_Flash-blue) ![Stack](https://img.shields.io/badge/Stack-FastAPI_React_Firebase-orange) ![Status](https://img.shields.io/badge/Status-Production_Ready-green)

---

## 🚀 Key Features

*   **🧠 RAG-Powered Chatbot:** Ask natural language questions about your supply chain (e.g., *"How many S2 scooters can we build?"*) and get answers based on real-time data.
*   **📊 Inventory Intelligence:** Monitors stock levels across multiple warehouses and flags shortages (Quantity < 60 units).
*   **🚨 Automatic Risk Detection:** Identifies blocked parts (Quality Issues, Safety Recalls) and delayed Purchase Orders.
*   **☁️ Cloud-Native:** Fully integrated with **Firebase Realtime Database** for live data sync.
*   **⚡ Modern Detection Engine:** Python-based logic to safeguard production capacity.

---

## 🛠️ Tech Stack

### Backend
*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **AI Engine:** LangChain + Google Gemini 1.5/2.5 Flash
*   **Database:** Firebase Admin SDK

### Frontend
*   **Framework:** React 19 (Vite)
*   **Styling:** Modern CSS (Glassmorphism, Dark Mode)
*   **State:** React Hooks

---

## 💻 Local Setup Guide

### 1. Prerequisites
*   Node.js (v18+)
*   Python (v3.10+)
*   Google Gemini API Key
*   Firebase Project Credentials

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
```
**Configuration (.env):**
Create `backend/.env`:
```ini
GEMINI_API_KEY=AIzaSy...
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_JSON=hugo-ai-credentials.json
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```
**Configuration (.env):**
Create `frontend/.env` (optional for local, required for cloud):
```ini
VITE_API_URL=http://localhost:8000
```

### 4. Run the App
**Option A: One-Click Script (Windows)**
Double-click `run_app.bat` in the root folder.

**Option B: Manual**
*   Terminal 1 (Backend): `uvicorn app.main:app --reload`
*   Terminal 2 (Frontend): `npm run dev`

---

## ☁️ Deployment (Render.com)

This project is configured for **One-Click Deployment** on Render using the Blueprint (`render.yaml`).

1.  Push code to GitHub.
2.  Go to **Render Dashboard** -> **New Blueprint**.
3.  Select your repo.
4.  Provide environment variables (`GEMINI_API_KEY`, `FIREBASE_SERVICE_ACCOUNT_BASE64`).
5.  Deploy! Use the provided **Deployment Guide** (`deployment.md`) for details on generating the Base64 credentials.

---

## 📁 Repository Structure

*   `backend/`: Python FastAPI application & AI logic.
*   `frontend/`: React application.
*   `hugo_data_samples/`: CSV datasets used to populate the Knowledge Base.
*   `render.yaml`: Infrastructure-as-Code for deployment.

---
*Built by Urjit Upadhyay*
