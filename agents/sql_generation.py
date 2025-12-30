"""
SQL Generation Agent
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

from utils.llm import call_llm
import json

def clean_sql(sql: str) -> str:
    """Clean SQL by removing markdown backticks, extra whitespace, and explanatory text"""
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
    
    # Extract only the first complete SQL statement
    # Look for SELECT, INSERT, UPDATE, DELETE, WITH as starting keywords
    sql = sql.strip()
    lines = sql.split('\n')
    
    statement_lines = []
    for line in lines:
        stripped = line.strip().upper()
        # Stop if we hit explanatory text (common patterns)
        if any(x in stripped for x in ['THE SQL', 'HERE IS', 'THIS QUERY', 'THE QUERY', 
                                        'FIRST PART', 'SECOND PART', 'FINALLY', 'UPDATE SQLITE',
                                        'THE FIRST', 'THE SECOND']):
            break
        # Stop at multiple SELECT statements (keep only first)
        if statement_lines and stripped.startswith('SELECT') and 'FROM' in ' '.join(statement_lines):
            break
        statement_lines.append(line)
    
    result = '\n'.join(statement_lines).strip()
    
    # Remove any remaining explanatory text after the query ends
    # Find the last semicolon and cut there
    if ';' in result:
        result = result.split(';')[0] + ';'
    
    return result.strip()

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
    print(sql)
    return clean_sql(sql)
