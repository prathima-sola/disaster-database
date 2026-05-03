# Global Disaster & Emergency Events Database

**ADT Final Project — Spring 2026, Indiana University Bloomington**

A web application for exploring, analyzing, and managing global natural disaster data from 1900 to 2021.

## Team
- Krishna Koushik Thokala — Database design, data preprocessing, query optimization
- Anirudh Sukumaran — Backend API, CRUD operations, deployment
- Prathima Sola — Frontend, data visualization, documentation

## Tech Stack
- **Backend:** Flask (Python)
- **Database:** SQLite 3
- **Frontend:** HTML/CSS/JavaScript, Chart.js, Leaflet.js
- **Deployment:** Render.com

## Data Sources
1. [EM-DAT via Kaggle](https://www.kaggle.com/datasets/brsdincer/all-natural-disasters-19002021-eosdis) — 16,126 disaster events
2. [World Bank Open Data](https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.CD) — GDP per capita & income group

## Features
- **Dashboard** with summary statistics and decade trends
- **Explore/Search** disasters with filters (country, type, year range, keyword)
- **Analytics** with 6 interactive charts + global disaster map
- **CRUD** — Create, Read, Update, Delete disaster events
- **Detail View** with impact metrics and location map

## Setup (Local)
```bash
pip install -r requirements.txt
python init_db.py          # Creates and populates the SQLite database
python app.py              # Runs on http://localhost:5000
```

## AI Acknowledgement
- Tool: Claude, by Anthropic (Claude Opus 4.6)
- Scope: Database schema design, SQL query generation, data preprocessing, documentation
