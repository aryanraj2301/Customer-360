from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

PROJECT_ROOT = "/opt/airflow/project"
with DAG(
    dag_id="customer360_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:

    generate_data = BashOperator(
        task_id="generate_synthetic_data",
        bash_command=f'python "{PROJECT_ROOT}/data-generation/customer_generation.py"',
    )

    load_bronze = BashOperator(
        task_id="load_bronze",
        bash_command=f'python "{PROJECT_ROOT}/data-generation/load_bronze.py"',
    )

    run_dbt = BashOperator(
        task_id="run_dbt_silver_gold",
        bash_command=f'cd "{PROJECT_ROOT}/dbt_project" && dbt run && dbt test',
    )

    generate_data >> load_bronze >> run_dbt