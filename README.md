# ⚽ Football Data Pipeline

> End-to-end data engineering project ingesting football data (World Cup, Brasileirão, Champions League) from a REST API, orchestrated with Apache Airflow, transformed with dbt, and visualized with Metabase — all running locally via Docker.

---

## 📌 About the Project

This project was built as a **data engineering portfolio**, covering the full lifecycle of a modern data pipeline:

- **Ingestion** — REST API consumption with Python (`requests`, `tenacity`)
- **Storage** — Raw data persisted in PostgreSQL
- **Transformation** — Layered modeling with dbt-core (staging → intermediate → marts)
- **Orchestration** — DAGs scheduled in Apache Airflow
- **Quality** — Unit tests with `pytest` + data tests with dbt
- **CI/CD** — Automated checks via GitHub Actions
- **Visualization** — Dashboards in Metabase (self-hosted)

Data source: [football-data.org](https://www.football-data.org/) — free tier (no credit card required).

---

## 🏗️ Architecture

```
football-data.org API
        │
        ▼
   Python (extraction scripts)
        │
        ▼
  PostgreSQL — schema: raw
        │
        ▼
   dbt-core
   ├── staging   (clean + typed)
   ├── intermediate  (business logic)
   └── marts     (analytical tables)
        │
        ▼
   Apache Airflow (orchestration)
        │
        ▼
   Metabase (dashboards)
        │
        ▼
   GitHub Actions (CI/CD)
```

---

## 🗂️ Project Structure

```
football-data-pipeline/
├── airflow/
│   ├── dags/
│   │   └── football_pipeline_dag.py
│   └── docker-compose.yml
├── dbt/
│   └── football_project/
│       ├── models/
│       │   ├── staging/
│       │   ├── intermediate/
│       │   └── marts/
│       ├── tests/
│       └── dbt_project.yml
├── extraction/
│   ├── extract_api.py
│   ├── load_to_postgres.py
│   └── utils.py
├── tests/
│   └── test_extraction.py
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Tool | Version |
|---|---|---|
| Language | Python | 3.11+ |
| Orchestration | Apache Airflow | 2.9+ |
| Transformation | dbt-core + dbt-postgres | 1.8+ |
| Database | PostgreSQL | 15+ |
| Containerization | Docker + Docker Compose | - |
| Testing | pytest | - |
| Linting | ruff + black | - |
| CI/CD | GitHub Actions | - |
| Visualization | Metabase (self-hosted) | - |

---

## 🚀 How to Run Locally

### Prerequisites

- Docker and Docker Compose installed
- A free API token from [football-data.org](https://www.football-data.org/client/register)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/football-data-pipeline.git
cd football-data-pipeline
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your FOOTBALL_API_TOKEN
```

### 3. Start the containers

```bash
docker-compose up -d
```

This will start:
- PostgreSQL on `localhost:5432`
- Airflow Webserver on `localhost:8080`
- Metabase on `localhost:3000`

### 4. Access Airflow

Open [http://localhost:8080](http://localhost:8080) with credentials `airflow / airflow`.
Enable and trigger the `football_pipeline` DAG.

### 5. Access Metabase

Open [http://localhost:3000](http://localhost:3000) and connect to the PostgreSQL database configured in `.env`.

---

## 📊 Covered Competitions (free tier)

| Competition | Code |
|---|---|
| FIFA World Cup | `WC` |
| Brasileirão Série A | `BSA` |
| UEFA Champions League | `CL` |
| Premier League | `PL` |
| La Liga | `PD` |
| Bundesliga | `BL1` |
| Serie A | `SA` |

---

## 🧪 Running Tests

```bash
# Python unit tests
pytest tests/

# dbt data tests
cd dbt/football_project
dbt test
```

---

## 📖 dbt Documentation

```bash
cd dbt/football_project
dbt docs generate
dbt docs serve
```

Open [http://localhost:8080](http://localhost:8080) to browse the full data lineage.

---

## 🔄 CI/CD

Every push or pull request to `main` triggers a GitHub Actions workflow that:

1. Lints Python code with `ruff`
2. Runs `pytest` unit tests
3. Validates dbt models with `dbt compile`

---

## 📌 Environment Variables

Create a `.env` file based on `.env.example`:

```env
# API
FOOTBALL_API_TOKEN=your_token_here

# PostgreSQL
POSTGRES_USER=football
POSTGRES_PASSWORD=football123
POSTGRES_DB=football_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Airflow
AIRFLOW_UID=50000
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

---

## 🗺️ Roadmap

- [x] Project structure and documentation
- [ ] API extraction scripts (Python)
- [ ] Raw layer loading (PostgreSQL)
- [ ] dbt staging models
- [ ] dbt intermediate models
- [ ] dbt marts models
- [ ] Airflow DAG
- [ ] pytest unit tests
- [ ] GitHub Actions CI workflow
- [ ] Metabase dashboards

---

## 👤 Author

**Your Name**
[LinkedIn](https://linkedin.com/in/yourprofile) · [GitHub](https://github.com/yourusername)

---

## 📄 License

This project is licensed under the MIT License.
Data provided by [football-data.org](https://www.football-data.org/).
