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
    sql = sql.strip()
    lines = sql.split('\n')
    
    statement_lines = []
    query_started = False
    select_count = 0
    
    for line in lines:
        stripped = line.strip().upper()
        
        # Skip empty lines at the start
        if not query_started and not stripped:
            continue
        
        # Mark that we've started the query
        if stripped.startswith(('SELECT', 'WITH', 'INSERT', 'UPDATE', 'DELETE')):
            query_started = True
        
        # Stop if we hit explanatory text patterns
        if query_started and any(x in stripped for x in ['THIS PLAN', 'QUERY FOR', '1.', '2.', 'HERE IS', 
                                                          'FIRST PART', 'SECOND PART', 'FINALLY',
                                                          'THE FIRST', 'THE SECOND', 'THE SQL']):
            # If it's a numbered list marker like "1. Query", stop
            if stripped and (stripped[0].isdigit() or 'QUERY FOR' in stripped):
                break
        
        # Detect multiple separate queries
        if query_started and stripped.startswith('SELECT'):
            select_count += 1
            if select_count > 1:  # Second SELECT statement detected
                break
        
        if query_started:
            statement_lines.append(line)
        
        # Stop at semicolon (end of statement)
        if query_started and ';' in line:
            break
    
    result = '\n'.join(statement_lines).strip()
    
    # Ensure we end with semicolon
    if result and not result.endswith(';'):
        result += ';'
    
    return result.strip()

def sql_generation_agent(
    schema_context: dict,
    query_plan: dict,
    retrieved_examples: str = "",
    previous_sql: str = "",
    error_feedback: str = ""
) -> str:
    system_prompt = open("prompts/sql_generation_system.txt").read()

    error_context = ""
    if previous_sql and error_feedback:
        error_context = f"""

PREVIOUS ATTEMPT THAT FAILED:
SQL: {previous_sql}
Error: {error_feedback}

Generate a corrected SQL query that fixes the above error."""

    user_prompt = f"""
APPROVED TABLES AND COLUMNS:
{json.dumps(schema_context, indent=2)}

PLAN TO IMPLEMENT:
{json.dumps(query_plan, indent=2)}{error_context}

Write SQLite SQL that implements this plan. Return ONLY the SQL query, nothing else:"""

    raw_response = call_llm(system_prompt, user_prompt).strip()
    print(f"\n[DEBUG] Raw LLM Response (length: {len(raw_response)}):")
    print(f"[DEBUG] {repr(raw_response[:500])}")  # Print first 500 chars with repr to see whitespace
    print(f"[DEBUG] Full response:\n{raw_response}\n")
    
    cleaned = clean_sql(raw_response)
    print(f"[DEBUG] Cleaned SQL (length: {len(cleaned)}):")
    print(f"[DEBUG] {cleaned}\n")
    
    # Check if multiple queries were detected
    semicolon_count = cleaned.count(';')
    if semicolon_count > 1:
        raise ValueError(f"SQL generator produced multiple queries or invalid format. This agent generates ONLY single queries. If your question requires multiple queries, rephrase it as a single combined query. Raw: {cleaned}")
    
    return cleaned
