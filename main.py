"""
Text-to-SQL Agents in Practice
Author: Mayank Goyal
Description: Multi-agent system to convert natural language questions to SQL queries
Reference: "Text-to-SQL Agents in Practice"
"""

from agents.schema_linking import schema_linking_agent
from agents.planning import planning_agent
from agents.sql_generation import sql_generation_agent
from agents.verification import verification_agent
from agents.correction import correction_agent
from execution.run_query import execute_sql
from query_memory.store import retrieve, add
import json
import sqlite3

DB_PATH = "data/chinook.db"
MAX_CORRECTIONS = 2

def get_schema_from_db():
    """Extract schema from actual database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_text = "CHINOOK DATABASE SCHEMA\n\nTables:\n\n"
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema_text += f"{table_name}:\n"
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            schema_text += f"  - {col_name} ({col_type})\n"
        schema_text += "\n"
    
    conn.close()
    return schema_text

SCHEMA = get_schema_from_db()

def run_text_to_sql_pipeline(question: str) -> dict:
    retrieved_examples = retrieve(question)

    schema_context = schema_linking_agent(question, SCHEMA)
    plan = planning_agent(question, schema_context)

    sql = sql_generation_agent(schema_context, plan, retrieved_examples)

    for _ in range(MAX_CORRECTIONS):
        verification = verification_agent(schema_context, plan, sql)
        if verification["is_valid"]:
            break

        correction = correction_agent(
            schema_context,
            plan,
            sql,
            verification
        )

        if correction["action"] != "correct_sql":
            return {"status": "failed", "reason": correction}

        sql = correction["corrected_sql"]

    execution = execute_sql(DB_PATH, sql)

    if execution["success"]:
        add(question, sql)

    return {
        "status": "success",
        "sql": sql,
        "result": execution
    }

if __name__ == "__main__":
    print("Initializing schema from database...")
    print("Tables available:", [t[0] for t in sqlite3.connect(DB_PATH).cursor().execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()])
    
    while True:
        q = input("\nAsk a question (or exit): ")
        if q.lower() == "exit":
            break
        result = run_text_to_sql_pipeline(q)
        print(json.dumps(result, indent=2))
