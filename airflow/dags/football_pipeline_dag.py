"""
football_pipeline_dag.py
------------------------
Orchestrates the full football data pipeline:
  1. Extract data from football-data.org API
  2. Load raw JSON into PostgreSQL
  3. Run dbt models
  4. Run dbt tests
"""
 
import sys
import os
from datetime import datetime, timedelta
 
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
 
# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
 
default_args = {
    "owner": "rodrigo",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
 
# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
 
with DAG(
    dag_id="football_pipeline",
    description="Extract → Load → Transform pipeline for football data (World Cup & Brasileirão)",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval="0 7 * * *",   # Every day at 07:00 UTC
    catchup=False,
    tags=["football", "etl", "dbt", "world-cup"],
) as dag:
 
    # -----------------------------------------------------------------------
    # Task 1 — Extract from API
    # -----------------------------------------------------------------------
    def extract(**context):
        sys.path.insert(0, "/opt/airflow/extraction")
        from import_api import run_extraction
        run_extraction(competition_codes=["WC", "BSA"])
 
    task_extract = PythonOperator(
        task_id="extract_from_api",
        python_callable=extract,
        doc_md="""
        ### Extract
        Calls football-data.org API and saves raw JSON files to `data/raw/`.
        Covers: FIFA World Cup (WC) and Brasileirão (BSA).
        """,
    )
 
    # -----------------------------------------------------------------------
    # Task 2 — Load to PostgreSQL
    # -----------------------------------------------------------------------
    def load(**context):
        sys.path.insert(0, "/opt/airflow/extraction")
        from load_to_postgres import run_load
        run_load(competition_codes=["WC", "BSA"])
 
    task_load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load,
        doc_md="""
        ### Load
        Reads raw JSON files and upserts data into PostgreSQL `raw` schema.
        Tables: matches, teams, standings, scorers.
        """,
    )
 
    # -----------------------------------------------------------------------
    # Task 3 — dbt run
    # -----------------------------------------------------------------------
    task_dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt/football_project && dbt run --profiles-dir /home/airflow/.dbt",
        doc_md="""
        ### dbt run
        Executes all dbt models:
        - staging: stg_matches, stg_teams, stg_standings, stg_scorers
        - intermediate: int_team_match_results
        - marts: fct_matches, mart_world_cup_summary
        """,
    )
 
    # -----------------------------------------------------------------------
    # Task 4 — dbt test
    # -----------------------------------------------------------------------
    task_dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt/football_project && dbt test --profiles-dir /home/airflow/.dbt",
        doc_md="""
        ### dbt test
        Runs all 21 data quality tests.
        Fails the DAG if any critical test fails.
        """,
    )
 
    # -----------------------------------------------------------------------
    # Pipeline order
    # -----------------------------------------------------------------------
    task_extract >> task_load >> task_dbt_run >> task_dbt_test