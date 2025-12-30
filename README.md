# 🤖 Hugo AI - Procurement Operations Agent

> AI-powered procurement assistant for Voltway Electric Scooters
> Built for the Dryft Hackathon

![Hugo AI](https://img.shields.io/badge/AI-Gemini%201.5-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![React](https://img.shields.io/badge/React-18-blue)

## 🎯 What is Hugo?

Hugo is an intelligent procurement agent that:
- ✅ **Monitors** supplier operations automatically
- ✅ **Detects** problems BEFORE they become crises
- ✅ **Calculates** financial impact
- ✅ **Generates** actionable recommendations
- ✅ **Explains** reasoning in plain English

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API Key ([Get one here](https://aistudio.google.com/))

### Step 1: Setup Backend

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
copy .env.example .env
# Then edit .env and add your GEMINI_API_KEY
```

### Step 2: Configure Environment

Edit `backend/.env`:
```env
GEMINI_API_KEY=your_actual_api_key_here
DATABASE_URL=sqlite:///./hugo.db
```

### Step 3: Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Step 4: Start Frontend

```bash
# Open new terminal
cd frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

## 📊 Features - Supplier Alert Categories

### 1. 🚚 Supplier Delay Detection
- Detects when deliveries are late
- Parses supplier emails for delay notifications
- Calculates days until stockout
- Identifies affected customer orders

### 2. 💰 Price Spike Detection
- Monitors price changes across purchase orders
- Alerts when prices increase >5% from baseline
- Calculates annual cost impact

### 3. 🏦 Financial Distress Detection
- Analyzes supplier emails for warning signs
- Detects payment term changes
- Flags suppliers requesting advance payments

### 4. 🔧 Quality Issue Pattern
- Tracks quality complaints from emails
- Alerts when patterns emerge
- Recommends inspection and corrective actions

## 🏗️ Project Structure

```
hugo/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # Database models
│   │   ├── database.py          # Database connection
│   │   ├── data_loader.py       # Load CSV data
│   │   ├── analyzers/
│   │   │   ├── supplier_analyzer.py
│   │   │   └── inventory_analyzer.py
│   │   ├── alerts/
│   │   │   └── alert_engine.py  # Main detection engine
│   │   └── ai/
│   │       └── gemini_client.py # Gemini API integration
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AlertList.jsx
│   │   │   ├── AlertCard.jsx
│   │   │   └── Toast.jsx
│   │   └── index.css
│   └── package.json
└── data/
    └── voltway_data/
        ├── materials.csv
        ├── stock_levels.csv
        ├── material_orders.csv
        ├── sales_orders.csv
        ├── supplier_emails.txt
        ├── dispatch_params.csv
        └── scooter_specs/
            ├── s1_classic.md
            ├── s2_v2.md
            └── s2_pro.md
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/alerts` | GET | Get all active alerts |
| `/alerts/refresh` | POST | Run detection engine |
| `/alerts/{id}/dismiss` | POST | Dismiss an alert |
| `/stats` | GET | Get dashboard statistics |
| `/suppliers` | GET | List all suppliers |
| `/materials` | GET | List all materials |
| `/purchase-orders` | GET | List purchase orders |
| `/sales-orders` | GET | List sales orders |
| `/data/reload` | POST | Reload data from CSVs |

## 🎬 Demo Script

1. **Open Dashboard** at http://localhost:5173
2. **Click "Run Detection"** to analyze current data
3. **View Generated Alerts** - see supplier delays, price spikes
4. **Expand Alert Details** - view impact analysis and recommendations
5. **Dismiss Alerts** - mark as handled

## 🔧 Configuration

### Using Your Own Dataset

Replace the files in `data/voltway_data/` with your own data:

1. `materials.csv` - Material master data
2. `stock_levels.csv` - Current inventory
3. `material_orders.csv` - Purchase orders
4. `sales_orders.csv` - Customer orders
5. `supplier_emails.txt` - Supplier communications
6. `scooter_specs/*.md` - Bill of Materials

Then call the reload endpoint:
```bash
curl -X POST http://localhost:8000/data/reload
```

## 🧠 How the AI Works

1. **Detection Engine** scans data for patterns (delays, price changes)
2. **Impact Calculator** determines financial/operational effects
3. **Gemini AI** enriches alerts with:
   - Human-readable explanations
   - Context-aware recommendations
   - Prioritized action items

**Built with ❤️ by the  Team dryfto**
