# Web-Spy 🕵️ - Competitive Intelligence Platform

A full-stack web application for monitoring competitors' websites, analyzing SEO, tracking content/pricing changes, and identifying market opportunities.

![Web-Spy Dashboard](https://via.placeholder.com/800x400?text=Web-Spy+Dashboard)

## 🚀 Features

- **Dashboard** - Real-time metrics, scan progress, competitor overview, and health scores
- **Competitors Management** - Add, monitor, and analyze competitor websites
- **SEO Analyzer** - On-page, technical, and content SEO analysis
- **Content Tracker** - Monitor page changes and content updates
- **Price Monitor** - Track pricing changes with historical charts
- **Product Watcher** - Monitor product catalogs and availability
- **Gap Finder** - Identify feature, content, and keyword opportunities
- **Alerts System** - Real-time notifications for competitor changes

## 🛠 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.11) |
| **Frontend** | React 18 + Vite + TailwindCSS |
| **Database** | PostgreSQL 15 + SQLAlchemy 2.0 |
| **Crawling** | Playwright (async) + BeautifulSoup4 |
| **Task Queue** | Celery + Redis |
| **Charts** | Recharts |
| **Deployment** | Docker + docker-compose |

## 📦 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Using Docker (Recommended)

```bash
# Clone the repository
cd "d:\Cursor project\Competitor analyzer"

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

The application will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Local Development

#### Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

#### Database & Redis
```bash
# Start only database services
docker-compose up -d postgres redis
```

#### Celery Workers
```bash
cd backend

# Start worker
celery -A app.tasks worker --loglevel=info

# Start beat scheduler (in separate terminal)
celery -A app.tasks beat --loglevel=info
```

## 📁 Project Structure

```
web-spy/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini              # Database migrations config
│   ├── alembic/                 # Migration scripts
│   ├── scripts/
│   │   └── cli.py               # CLI utility
│   └── app/
│       ├── main.py              # FastAPI app + WebSocket
│       ├── config.py            # Settings
│       ├── database.py          # SQLAlchemy setup
│       ├── websocket.py         # Real-time updates
│       ├── models/              # Database models
│       ├── api/                 # API routes
│       ├── services/            # Business logic
│       │   ├── crawler.py       # Playwright web crawler
│       │   ├── seo_analyzer.py  # SEO analysis
│       │   ├── content_tracker.py  # Content change detection
│       │   ├── price_monitor.py # Price tracking
│       │   ├── product_watcher.py  # Product monitoring
│       │   └── gap_finder.py    # Opportunity analysis
│       └── tasks/               # Celery tasks
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── App.tsx
        ├── pages/               # Page components
        ├── components/          # UI components
        ├── services/            # API client
        └── hooks/               # Custom hooks (WebSocket)
```

## 🖥️ CLI Commands

The CLI utility provides quick access to common operations:

```bash
cd backend

# Initialize database
python scripts/cli.py init

# Add a competitor
python scripts/cli.py add "Acme Inc" "https://acme.com" --type direct

# List all competitors
python scripts/cli.py list

# Trigger a full scan
python scripts/cli.py scan <competitor-id>

# Quick scan a URL
python scripts/cli.py quick https://example.com

# Analyze SEO
python scripts/cli.py seo https://example.com

# Show statistics
python scripts/cli.py stats
```

## 🔧 Configuration

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://webspy:webspy_secret@localhost:5432/webspy_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/dashboard/metrics` | Dashboard metrics |
| `GET /api/competitors` | List competitors |
| `POST /api/competitors` | Add competitor |
| `POST /api/competitors/{id}/scan` | Trigger scan |
| `GET /api/seo/{id}` | SEO analysis |
| `GET /api/content/{id}` | Content tracking |
| `GET /api/prices/{id}` | Price history |
| `GET /api/alerts` | Alerts list |

Full API documentation at http://localhost:8000/docs

## 🎨 UI Features

- **Glass Morphism Design** - Modern, premium aesthetic
- **Dark Theme** - Easy on the eyes
- **Responsive Layout** - Works on all screen sizes
- **Real-time Updates** - Live scan progress
- **Interactive Charts** - Recharts visualizations
- **Smooth Animations** - Micro-interactions

## 🔒 Web Scraping Best Practices

The crawler is configured with:
- ✅ Robots.txt compliance
- ✅ Rate limiting (configurable delays)
- ✅ User-agent rotation
- ✅ Resource blocking for performance
- ✅ Exponential backoff retry logic
- ✅ Concurrent but respectful crawling

## 📄 License

MIT License - feel free to use for any purpose.

---

Built with ❤️ using FastAPI, React, and Playwright
