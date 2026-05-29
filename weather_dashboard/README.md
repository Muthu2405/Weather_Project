# 🌤️ Weather Live Dashboard

A real-time auto-refreshing weather dashboard built with Flask + Chart.js, backed by PostgreSQL.

---

## 📁 Project Structure

```
weather_dashboard/
├── app.py              # Flask backend + REST API
├── templates/
│   └── index.html      # Dashboard UI (Chart.js + vanilla JS)
├── requirements.txt    # Python dependencies
├── Procfile            # For Railway deployment
├── render.yaml         # For Render deployment
└── .env                # DB credentials (not committed)
```

---

## ⚙️ Local Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Create `.env`
```env
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=weather_db
```

### 3. Run locally
```bash
python app.py
```
Open: http://localhost:5000

---

## 🚀 Deploy to Render (Free)

1. Push this folder to a GitHub repo
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set environment variables (DB_USER, DB_PASSWORD, DB_HOST, etc.)
5. Deploy — Render auto-detects the Procfile

> For the database, use [Neon.tech](https://neon.tech) — free PostgreSQL in the cloud.

---

## 🚀 Deploy to Railway (Free)

1. Push to GitHub
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Add a PostgreSQL plugin
4. Set environment variables
5. Deploy!

---

## 📡 API Endpoints

| Endpoint | Description |
|---|---|
| `GET /` | Dashboard UI |
| `GET /api/latest` | Most recent weather record |
| `GET /api/forecast` | All records (7-day) |
| `GET /api/stats` | Aggregate stats |

---

## 🔄 Auto-Refresh

The dashboard auto-refreshes every **30 seconds** — no page reload needed.
The spinning ring in the header indicates a data fetch in progress.
