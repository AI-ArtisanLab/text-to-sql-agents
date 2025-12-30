"""
Correction Agent
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

import json
from utils.llm import call_llm

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

def correction_agent(
    schema_context: dict,
    query_plan: dict,
    sql: str,
    verification_issues: dict,
    execution_feedback: str = "",
    distinct_values: dict | None = None
) -> dict:
    system_prompt = open("prompts/correction.txt").read()

    user_prompt = f"""
SCHEMA CONTEXT
{json.dumps(schema_context, indent=2)}

QUERY PLAN
{json.dumps(query_plan, indent=2)}

GENERATED SQL
{sql}

VERIFICATION ISSUES
{json.dumps(verification_issues, indent=2)}

EXECUTION FEEDBACK
{execution_feedback or "None"}

KNOWN DISTINCT VALUES
{json.dumps(distinct_values, indent=2) if distinct_values else "None"}
"""

    response = call_llm(system_prompt, user_prompt)
    result = json.loads(response)
    
    # Clean the corrected SQL if present
    if result.get("action") == "correct_sql" and "corrected_sql" in result:
        result["corrected_sql"] = clean_sql(result["corrected_sql"])
    
    return result
