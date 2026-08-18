# Customer 360 Lakehouse

An end-to-end data platform that unifies fragmented customer data — CRM, orders, support tickets, and web events — into a single, trusted **Customer 360** view. Built on a modern lakehouse architecture (medallion pattern), fully orchestrated, tested, and served through a live dashboard.

---

## Table of Contents

- [Problem](#problem)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Data Model](#data-model)
- [Identity Resolution](#identity-resolution)
- [The Gold Table](#the-gold-table)
- [Project Structure](#project-structure)
- [Running It Locally](#running-it-locally)
- [Running the Automated Pipeline (Airflow)](#running-the-automated-pipeline-airflow)
- [Dashboard](#dashboard)
- [Data Quality / Tests](#data-quality--tests)
- [Challenges Faced](#challenges-faced)
- [What I'd Improve Next](#what-id-improve-next)
- [Screenshots](#screenshots)

---

## Problem

Real companies scatter customer data across disconnected systems: a CRM holds contact info, an orders database holds purchase history, a support tool holds tickets, and web analytics holds behavioral events. Each system only has a partial view of the customer, and the same person is often represented inconsistently — different IDs, an email in one system and a customer ID in another, typos, or an anonymous cookie ID before login.

**Customer 360** is the practice of resolving that fragmentation into one accurate, unified profile per customer, used for personalization, support context, churn prediction, and marketing. This project builds the full pipeline that does exactly that — from raw, messy synthetic data all the way to an automated, tested, dashboarded platform.

## Architecture

This follows the **medallion architecture** — the industry-standard way of organizing a lakehouse:

```
Synthetic Sources (CRM, Orders, Tickets, Web Events)
        │
        ▼
   BRONZE   →  raw, as-landed, no transformations   (DuckDB)
        │
        ▼
   SILVER   →  cleaned, deduplicated, identity-resolved   (dbt)
        │
        ▼
   GOLD     →  business-ready Customer 360 table, tested   (dbt)
        │
        ▼
   Streamlit Dashboard  ←  served to end users
```

The entire chain — synthetic data generation → Bronze load → Silver/Gold transformation → tests — runs automatically end-to-end via an **Airflow DAG**, containerized with **Docker**, so it's a real orchestrated platform rather than a set of scripts run by hand.

## Tech Stack

| Layer | Tool | Why this tool |
|---|---|---|
| Data generation | Python + Faker | Realistic, privacy-safe synthetic data standing in for real CRM/order/support/web systems |
| Storage / query engine | DuckDB | Zero-infrastructure, fast local OLAP engine acting as the lakehouse's storage + compute layer |
| Transformation | dbt-core | Version-controlled, testable SQL transformations — the industry-standard modeling tool |
| Orchestration | Apache Airflow (Docker) | Scheduled, automated, monitorable, retry-capable pipeline execution |
| Dashboard | Streamlit | Fast, code-first BI layer directly on top of the Gold table |
| Version control | Git + GitHub | Full history, portfolio visibility |

**Why DuckDB instead of Spark/cloud warehouses?** For a project this size, DuckDB gives all the SQL power and ACID-safe table behavior needed to learn and demonstrate the medallion pattern, with zero cluster/cloud cost or setup — the same dbt models here can be pointed at Snowflake, BigQuery, or Databricks with only a `profiles.yml` change, since dbt abstracts the warehouse layer.

## Data Model

Four source entities, each with a deliberately realistic "grain" (one row = one real-world event):

| Table | Grain | Notes |
|---|---|---|
| `customers` | one row per customer | the CRM system of record |
| `orders` | one row per order | linked to `customers` |
| `order_items` | one row per product line in an order | linked to `orders` |
| `support_tickets` | one row per ticket | **deliberately messy** — references either `customer_id` or raw `email` |
| `web_events` | one row per event (page view, cart add, etc.) | **deliberately messy** — mix of known `customer_id` and anonymous cookie IDs |

The messiness in `support_tickets` and `web_events` is intentional — it simulates how real systems reference customers inconsistently, which is exactly the problem identity resolution exists to solve.

## Identity Resolution

The hardest part of Customer 360 isn't the ETL — it's recognizing that `CUST00042`, `john.doe@email.com`, and an anonymous web cookie might all be the same person.

The **Silver layer** (`silver_identity_map.sql`) resolves this:
- Matches support tickets to a real `customer_id` via **email**, when the ticket stored an email instead of an ID
- Tracks the **match method** per record (`matched_by_email` vs. passthrough) for auditability — a real production system needs to know *how* it resolved an identity, not just that it did
- Currently uses **deterministic (exact) matching**; see [What I'd Improve Next](#what-id-improve-next) for the planned fuzzy-matching upgrade

## The Gold Table

`gold_customer_360` — one row per customer, aggregated from every source:

| Column | Meaning |
|---|---|
| `customer_id`, `full_name`, `email`, `signup_date` | core identity |
| `total_orders`, `lifetime_value`, `last_order_date` | purchase behavior |
| `total_tickets`, `avg_csat` | support engagement |
| `churn_risk_flag` | rule-based: true if no order in 90+ days or never ordered |

This is the table a marketing, support, or analytics team would actually query — and it's what powers the dashboard.

## Project Structure

```
customer360/
  data-generation/
    customer_generation.py   # generates all 5 synthetic source CSVs
    load_bronze.py           # loads CSVs into DuckDB as the Bronze layer
  dbt_project/
    models/
      sources.yml             # declares Bronze tables as dbt sources
      silver/
        silver_orders.sql
        silver_identity_map.sql
      gold/
        gold_customer_360.sql
        schema.yml            # dbt tests (uniqueness, not-null)
    profiles.yml               # dbt connection profile (container-portable)
  airflow/
    Dockerfile                 # custom image: Airflow + faker/duckdb/dbt-duckdb
    docker-compose.yaml
    dags/
      customer360_pipeline.py  # orchestrates generate → load → transform → test
  dashboard/
    app.py                     # Streamlit dashboard on the Gold table
  warehouse/
    customer360.duckdb         # local lakehouse file (gitignored)
```

## Running It Locally

```bash
# 1. Set up environment
python -m venv venv
source venv/bin/activate        # or venv\Scripts\Activate.ps1 on Windows
pip install faker duckdb pandas dbt-duckdb streamlit

# 2. Generate synthetic data and load Bronze
python data-generation/customer_generation.py
python data-generation/load_bronze.py

# 3. Build Silver + Gold with dbt, and run tests
cd dbt_project
dbt run
dbt test

# 4. Launch the dashboard
cd ../dashboard
streamlit run app.py
```

## Running the Automated Pipeline (Airflow)

The whole pipeline above also runs automatically, containerized:

```bash
cd airflow
docker compose up airflow-init
docker compose up -d
```

Open `http://localhost:8080` (login `airflow`/`airflow`), unpause and trigger the `customer360_pipeline` DAG. It runs three tasks in order — `generate_synthetic_data` → `load_bronze` → `run_dbt_silver_gold` — with full logging and retry support.

## Dashboard

The Streamlit app reads directly from the Gold table and shows:
- Key metrics: total customers, total lifetime value, at-risk customer count
- The full Customer 360 table
- A lifetime-value distribution chart

## Data Quality / Tests

`dbt test` enforces:
- `unique` — no duplicate `customer_id` in the Gold table
- `not_null` — every customer row has a valid ID

These run automatically as part of the Airflow DAG, so a broken pipeline run is caught before bad data reaches the dashboard.

## Challenges Faced

Building this end-to-end surfaced real infrastructure problems, not just modeling ones:
- **Environment/interpreter mismatches** — multiple Python installs (a pre-release alpha version via `uv`, plus a stable install) caused packages to install in one environment while scripts ran from another; solved by standardizing on one explicit interpreter and always running from an activated terminal.
- **Airflow inside Docker can't see the host filesystem by default** — required a custom `Dockerfile` (to install `faker`/`duckdb`/`dbt-duckdb` into the Airflow image) plus an explicit volume mount to expose the project folder inside the container at a Linux path.
- **dbt inside the container couldn't find its connection profile** — the local `~/.dbt/profiles.yml` only exists on the host machine; fixed by shipping a container-portable `profiles.yml` inside the dbt project itself and pointing `dbt` at it via `DBT_PROFILES_DIR`.
- **~80 bundled Airflow example DAGs** made the real pipeline hard to find in the UI — solved by searching explicitly and later disabling `AIRFLOW__CORE__LOAD_EXAMPLES`.

## What I'd Improve Next

- **Upgrade identity resolution to fuzzy matching** (e.g. via `rapidfuzz`) for cases where names/emails don't match exactly — currently only exact-match resolution is implemented.
- **Inject known duplicate customers** into the synthetic data so match accuracy can be measured with a real, quotable number (e.g. "resolved X% of injected duplicates correctly").
- **Cloud migration** — swap the local DuckDB file for S3-backed storage and Databricks/Snowflake compute; the dbt models are already warehouse-agnostic.
- **Deploy the dashboard publicly** (e.g. Streamlit Community Cloud) so it's viewable without cloning the repo.

## Screenshots

*(Add a screenshot or short GIF of the Streamlit dashboard here — e.g. `docs/dashboard-screenshot.png`)*
