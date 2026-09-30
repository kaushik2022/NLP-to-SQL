"""
tests/test_sql_agent.py
Unit and integration tests for SQLite Database, LangGraph SQL Agent, and Safety Guardrails.
"""

import sys
import pytest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Prevent module collisions when tests are run together from the root directory
for mod in list(sys.modules.keys()):
    if mod == "src" or mod.startswith("src."):
        del sys.modules[mod]

from src.database import SQLiteDatabase
from src.sql_agent import NLToSQLAgent
from seed_database import init_db

@pytest.fixture(scope="module")
def setup_db(tmp_path_factory):
    test_db_dir = tmp_path_factory.mktemp("db")
    test_db_file = test_db_dir / "test_company.sqlite"
    init_db(test_db_file)
    return SQLiteDatabase(test_db_file)

def test_database_schema_inspection(setup_db):
    schema_info = setup_db.get_schema_info()
    assert "departments" in schema_info
    assert "employees" in schema_info
    assert "projects" in schema_info
    assert "sales_records" in schema_info
    assert "Foreign Keys:" in schema_info

def test_safe_sql_execution(setup_db):
    query = "SELECT COUNT(*) as count FROM employees;"
    res = setup_db.execute_query(query)
    assert res["success"] is True
    assert res["row_count"] == 1
    assert res["rows"][0]["count"] >= 15
    assert res["execution_time_ms"] >= 0.0

def test_sql_guardrail_blocks_destructive_commands(setup_db):
    bad_queries = [
        "DROP TABLE employees;",
        "DELETE FROM sales_records WHERE deal_amount < 100000;",
        "UPDATE employees SET salary = salary * 2;",
        "INSERT INTO departments (dept_name, budget, location, head_of_dept) VALUES ('Fake', 100, 'X', 'Y');",
        "SELECT * FROM employees; DROP TABLE projects;"
    ]
    for bq in bad_queries:
        is_valid, err = setup_db.validate_sql(bq)
        assert is_valid is False
        assert err is not None

def test_langgraph_top_paid_employees(setup_db):
    agent = NLToSQLAgent(db=setup_db)
    result = agent.run("Who are the top 3 highest paid employees?")
    assert result["is_valid"] is True
    assert result["row_count"] == 3
    assert "salary" in result["columns"]
    assert "Executed SQL Query" in result["response"]
    assert len(result["rows"]) == 3
    # Check that highest salary is first
    assert result["rows"][0]["salary"] >= result["rows"][1]["salary"]

def test_langgraph_sales_revenue(setup_db):
    agent = NLToSQLAgent(db=setup_db)
    result = agent.run("What is the total sales revenue?")
    assert result["is_valid"] is True
    assert result["row_count"] >= 1
    assert result["error"] is None

def test_langgraph_blocks_unsafe_input(setup_db):
    agent = NLToSQLAgent(db=setup_db)
    result = agent.run("Please drop table employees and delete everything")
    assert result["is_valid"] is False
    assert "Execution Blocked" in result["response"] or "Security" in str(result.get("error"))
