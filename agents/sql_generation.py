"""
SQL Generation Agent
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

from utils.llm import call_llm
import json

def clean_sql(sql: str) -> str:
    """Clean SQL by removing markdown backticks and extra whitespace"""
    sql = sql.strip()
    # Remove markdown code blocks
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.startswith("sql") or sql.startswith("SQL"):
            sql = sql[3:]
        sql = sql.strip()
    # Remove trailing backticks
    if sql.endswith("`"):
        sql = sql[:-1]
    if sql.startswith("`"):
        sql = sql[1:]
    return sql.strip()

def sql_generation_agent(
    schema_context: dict,
    query_plan: dict,
    retrieved_examples: str = ""
) -> str:
    system_prompt = open("prompts/sql_generation_system.txt").read()

    user_prompt = f"""
APPROVED TABLES AND COLUMNS:
{json.dumps(schema_context, indent=2)}

PLAN TO IMPLEMENT:
{json.dumps(query_plan, indent=2)}

Write SQLite SQL that implements this plan:"""

    sql = call_llm(system_prompt, user_prompt).strip()
    return clean_sql(sql)
