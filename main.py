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
MAX_VERIFICATION_CORRECTIONS = 2
MAX_EXECUTION_RETRIES = 3
MAX_FULL_PIPELINE_RETRIES = 2

def safe_format_list(items, item_formatter=str):
    """Safely format a list of items, handling both strings and dicts"""
    if not items:
        return ""
    if not isinstance(items, list):
        return str(items)
    
    formatted = []
    for item in items:
        if isinstance(item, str):
            formatted.append(item)
        elif isinstance(item, dict):
            formatted.append(item_formatter(item))
        else:
            formatted.append(str(item))
    return ', '.join(formatted)

def normalize_schema_context(schema_context: dict) -> dict:
    """Normalize schema context to use consistent key names"""
    normalized = {}
    
    # Handle tables (relevant_tables -> tables)
    normalized['tables'] = schema_context.get('tables') or schema_context.get('relevant_tables', [])
    
    # Handle columns (relevant_columns -> columns)
    normalized['columns'] = schema_context.get('columns') or schema_context.get('relevant_columns', {})
    
    # Handle relationships (relationships -> relationships)
    normalized['relationships'] = schema_context.get('relationships') or schema_context.get('relations', [])
    
    # Keep all other keys as is
    for key, value in schema_context.items():
        if key not in ['tables', 'relevant_tables', 'columns', 'relevant_columns', 'relationships', 'relations']:
            normalized[key] = value 
    
    return normalized

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
    print("\n" + "="*80)
    print(f"Question: {question}")
    print("="*80)

    #Step 1: Query Memory Retrieval (only once)
    print( "\nStep 1: Query Memory Retrieval")
    print(" Searching for similar queries in memory...")
    retrieved_examples = retrieve(question)
    if retrieved_examples:
        print(f" Found similar query in memory:\n{retrieved_examples}")
        print(" Will use as reference for SQL generation.")
    
    #Step 2: Schema Linking (only once- doesn't change with errors)
    print( "\nStep 2: Schema Linking Agent")
    print(" Identifying relevant tables and columns...")
    schema_linking = schema_linking_agent(question, SCHEMA)
    #Normalize schema context keys for consistent access
    schema_context = normalize_schema_context(schema_linking)

    #Debug: Show what keys were returned
    if not schema_context or len(schema_context) == 0:
        print(" Warning: Schema linking returned empty response.")

    #Display results using normalized keys
    tables = schema_context.get('tables', [])
    if tables:
        print(f" Relevant Tables: {safe_format_list(tables)}")
    else:
        print(" Warning: No relevant tables identified.")

    columns = schema_context.get('columns', {})
    if columns:
        print(f" Key Columns:")
        for table, cols in columns.items():
            col_names = [str(c) for c in cols[:5]] if isinstance(cols, list) else [str(cols)]
            print(f"  - {table}: {', '.join(col_names)}{'...' if isinstance(cols, list) and len(cols) > 5 else ''}")
    
    relationships = schema_context.get('relationships', [])
    if relationships:
        print(f" Relationships: {len(relationships)} joins identified.")
        for rel in relationships[:5]:
            if isinstance(rel, dict):
                #Handle format: {"from": "TableA.ColumnX", "to": "TableB.ColumnY"}
                from_field = rel.get("from", "Unknown")
                to_field = rel.get("to", "Unknown")
                print(f"  - {from_field} <-> {to_field}")
            elif isinstance(rel, str):
                print(f"  - {rel}")
            else:
                print(f"  - {str(rel)}")

    #Main pipeline loop- allows regeneration from planning stage
    error_feedback = "" # Accumulated error feedback for regeneration

    for pipeline_attempt in range(MAX_FULL_PIPELINE_RETRIES):
        if pipeline_attempt > 0:
            print("\n" + "-"*40)
            print(f"PIPELINE RETRY #{pipeline_attempt + 1}")
            print(f"Previous error will be used to improve the query.")
            print("-"*40 + "\n")

        #Step 3: Planning (Regenerated on retry with error feedback)
        print(f"\nStep 3: Planning Agent{'  -REGENERATING WITH ERROR FEEDBACK' if error_feedback else ''}")
        print("  Creating query execution plan...")
        if error_feedback:
            print(f" Error context:\n{error_feedback}")
        
        plan = planning_agent(question, schema_context)
        print(f" Query Type: {plan.get('query_type', 'Unknown')}")
        if plan.get('steps'):
            print(" Execution Steps:")
            for i, step in enumerate(plan.get('steps', [])[:5], 1):
                step_text = step if isinstance(step, str) else str(step)
                print(f"  {i}. {step_text}")

        if plan.get('aggregations'):
            # Formatting aggregations: handles strings, dicts, etc.
            def format_agg(agg):
                if isinstance(agg, str):
                    func = agg.get('function', agg.get('type', 'AGG'))
                    col = agg.get('column', agg.get('field', ''))
                    return f"{func}({col})" if col else func
                return str(agg)
            
            agg_display = safe_format_list(plan.get('aggregations', []), format_agg)
            if agg_display:
                print(f" Aggregations: {agg_display}")
        
        if plan.get('filters'):
            print(f"  Filters: {len(plan.get('filters', []))} conditions")

        #Step 4: SQL Generation (Regenerated with error feedback)
        print(f"\n STEP 4: SQL Generation Agent{' -WITH ERROR FEEDBACK' if error_feedback else ''}")
        print("  Generating SQL query...")
        try:
            sql = sql_generation_agent(schema_context, plan, retrieved_examples, error_feedback=error_feedback)
            print(f" Generated SQL:\n{sql}")
        except ValueError as e:
            print(f" ERROR: {str(e)}")
            error_feedback = str(e)
            continue  # Retry the entire pipeline

        # Step 5: Static verification and correction (up to MAX_VERIFICATION_CORRECTIONS times)
        print("\nSTEP 5: Verification Agent]")
        print("Checking SQL validity...")

        for attempt in range(MAX_VERIFICATION_CORRECTIONS):
            verification = verification_agent(schema_context, plan, sql)

            if verification["is_valid"]:
                print(f"SQL passed static verification")
                if verification.get('issues'):
                    print(f"Minor issues noted: {', '.join(verification['issues'][:3])}")
                print(f"\nSTEP 6: Correction Agent]")
                print("Skipped. No corrections needed")
                break  # Exit loop if no issues

            print(f"Verification failed (attempt {attempt + 1}/{MAX_VERIFICATION_CORRECTIONS})")
            print(f"Severity: {verification.get('severity', 'unknown')}")
            if verification.get('issues'):
                print("Issues found:")
                for issue in verification['issues'][:3]:
                    print(f"  {issue}")
                
            print(f"\n[STEP 6: Correction Agent Attempt {attempt + 1}]")
            print("Attempting to fix issues...")
            correction = correction_agent(schema_context, plan, sql, verification)
        
            if correction["action"] != "correct_sql":
                print(f" Correction failed: {correction.get('reasoning', 'Unknown reason')}")
                error_feedback = f"Verification failed: {', '.join(verification.get('issues', []))}. Correction failed: {correction.get('reasoning', 'Unknown')}."
                break # break verification-correction loop to regenerate entire pipeline

            sql = correction["corrected_sql"]
            print("SQL Corrected")
            if correction.get("reasoning"):
                print(f"Reasoning: {correction['reasoning']}")
            print(f"New SQL:\n{sql}")

        # Step 7: Execute and retry on errors (up to MAX_EXECUTION_RETRIES)
        print(f"\nSTEP 7: SQL Execution")
        print("Executing SQL against database...")
        execution_success = False

        for exec_attempt in range(MAX_EXECUTION_RETRIES):
            execution = execute_sql(DB_PATH, sql)

            if execution["success"]:
                print("SQL executed successfully.")
                
                #Display Results
                results_data = execution.get("data", [])
                print(f"\nSTEP 8: Query Results")
                print(f" Rows returned: {len(results_data)}")

                if results_data:
                    #Print first 5 rows
                    print("\n ResultsPreview:")
                    print(f"  {'-'*60}")
                    for i, row in enumerate(results_data[:10], 1): # Show up to 10 rows
                        print(f"  {i}. {row}")
                    if len(results_data) > 10:
                        print(f"  ... ({len(results_data) - 10} more rows)")
                    print(f"  {'-'*60}")
                else:
                    print(f" Query executed successfully but returned no rows.")
                    print(f"  This might be correct if the data doesn't exist as per the query conditions.")
            
                #Ask user confirmation before adding to memory
                print(f"\nSTEP 9: Save to Query Memory?")
                print(f" This query executed successfully!")
                print(f"  SQL: {sql}")

                # ASK for confirmation to save
                try:
                    user_input = input(" Do you want to save this query to memory for future reference? (yes/no): ").strip().lower()
                    if user_input in ['yes', 'y']:
                        add(question, sql)
                        print(" Query saved to memory.")
                    else:
                        print(" Query not saved to memory as per user choice.")
                except:
                    print(" No user input available. Skipping saving to memory.")

                print("\n" + "="*80)
                print("PIPELINE COMPLETED SUCCESSFULLY")
                print("="*80 + "\n")
                return {
                    "status": "success",
                    "sql": sql,
                    "result": execution,
                    "pipeline_attempts": pipeline_attempt + 1,
                    "excecution_attempts": exec_attempt + 1
                }

            #Execution failed
            print(f" Execution failed: (attempt {exec_attempt + 1}/{MAX_EXECUTION_RETRIES})")
            print(f" Error: {execution.get('error', 'Unknown error')}")

            if exec_attempt < MAX_EXECUTION_RETRIES - 1:
                print(f"\nStep 10: Correction Agent for Execution Errors Fix")
                print(" Analyzing execution error to fix SQL...")
                
                execution_verification = {
                    "is_valid": False,
                    "issues": [f"Execution error: {execution.get('error', 'Unknown error')}"],
                    "severity": "critical"
                }

                correction = correction_agent(
                    schema_context,
                    plan,
                    sql,
                    execution_verification,
                    execution_feedback=execution.get('error', '')
                )
                
                if correction["action"] == "correct_sql" and "corrected_sql" in correction:
                    sql = correction["corrected_sql"]
                    print("SQL Corrected for execution error.")
                    if correction.get("reasoning"):
                        print(f"Reasoning: {correction['reasoning']}")
                    print(f"New SQL:\n{sql}")
                else:
                    print(f" Correction failed: {correction.get('reasoning', 'Unknown reason')}")
                    print(f"  Action: {correction.get('action', 'Unknown')}")
                    error_feedback = f"Execution error: {execution.get('error', '')}. Previous SQL: {sql}"
                    error_feedback = f"Execution failed: {execution.get('error', 'Unknown error')}. Correction failed: {correction.get('reasoning', 'Unknown')}."
                    break  # break execution retry loop to regenerate entire pipeline
            else:
                print(" Maximum execution retries reached. Will regenerate entire pipeline.")
                error_feedback = f"Execution failed: {execution.get('error', 'Unknown error')} after {MAX_EXECUTION_RETRIES} attempts."

        #If we successfully executed, we already returned above
        # If we're here, it means execution failed after retries
        if pipeline_attempt < MAX_FULL_PIPELINE_RETRIES - 1:
            print(f"\n Will attempt full pipeline regeneration with error context.")
            continue
        else:
            break
    #IF we reach here, all attempts failed
    print("\n" + "="*80)
    print("PIPELINE FAILED AFTER ALL ATTEMPTS")
    print("="*80 + "\n")
    print(f"Error Feedback: {error_feedback}")

    return {
        "status": "failed",
        "reason": "All pipeline attempts exhausted.",
        "error_feedback": error_feedback,
        "sql": sql if 'sql' in locals() else None,
        "result": execution if 'execution' in locals() else None,
        "pipeline_attempts": pipeline_attempt + 1
    }

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TEXT-TO-SQL AGENTS PIPELINE")
    print("="*80 + "\n")
    print("Initializing schema from database...")
    tables = [t[0] for t in sqlite3.connect(DB_PATH).cursor().execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    print(f" Database loaded with {len(tables)} tables: {', '.join(tables)}\n")
    print("\n Type 'exit' to quit.\n")

    while True:
        q = input("\n" + "-"*80 + "\nAsk a question (or exit): ")
        if q.lower() == "exit":
            print("Exiting Text-to-SQL Agents Pipeline. Goodbye!")
            break
            
        result = run_text_to_sql_pipeline(q)

        if result["status"] != "success":
            print(f"\n" + "="*80)
            print(" FINAL RESULT: FAILURE SUMMARY")
            print("="*80 + "\n")
            print(f"\n Status: FAILED")
            print(f" Reason: {result.get('reason', 'Unknown')}")
            print(f" Pipeline Attempts: {result.get('pipeline_attempts', 0)}")
            if result.get("sql"):
                print(f" Last Generated SQL:\n{result['sql']}")
            if result.get("error_feedback"):
                print(f" Error details:\n{result['error_feedback']}")

