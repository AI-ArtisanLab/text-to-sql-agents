"""
SQL Query Execution
Author: Mayank Goyal
Reference: "Text-to-SQL Agents in Practice"
"""

import sqlite3

def execute_sql(db_path: str, sql: str) -> dict:
    """Execute SQL against the SQLite database and return results with detailed information"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        conn.close()

        data = []
        for row in rows:
            if cols:
                data.append(dict(zip(cols, row)))
            else:
                data.append(row)

        return {
            "success": True,
            "columns": cols,
            "rows": rows,
            "data": data,
            "row_count": len(data),
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "columns": [],
            "rows": [],
            "data": [],
            "row_count": 0,
            "error": str(e)
        }
