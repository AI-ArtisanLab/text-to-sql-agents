"""
SQL Query Execution
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

import sqlite3

def execute_sql(db_path: str, sql: str) -> dict:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        conn.close()
        return {
            "success": True,
            "columns": cols,
            "rows": rows,
            "row_count": len(rows),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": str(e)
        }
