"""
src/database.py
Local SQLite Database Engine and Schema Mapping Manager.
Handles schema inspection, SQL execution, timing, and security validation.
"""

import sqlite3
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

class SQLiteDatabase:
    """Manages SQLite database connections, schema extraction, and safe execution."""

    FORBIDDEN_KEYWORDS = [
        r"\bDROP\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
        r"\bALTER\b", r"\bTRUNCATE\b", r"\bEXEC\b", r"\bVACUUM\b",
        r"\bATTACH\b", r"\bDETACH\b", r"\bREPLACE\b"
    ]

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite database not found at {self.db_path}. Please run seed_database.py first.")

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema_info(self) -> str:
        """Dynamically inspects tables, column types, foreign keys, and sample rows."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_lines = ["=== DATABASE SCHEMA OVERVIEW ==="]
        
        for table in tables:
            schema_lines.append(f"\nTable: {table}")
            
            # Column info: cid, name, type, notnull, dflt_value, pk
            cursor.execute(f"PRAGMA table_info('{table}');")
            columns = cursor.fetchall()
            col_desc = []
            for col in columns:
                pk_marker = " [PRIMARY KEY]" if col[5] == 1 else ""
                notnull_marker = " NOT NULL" if col[3] == 1 else ""
                col_desc.append(f"  - {col[1]} ({col[2]}){pk_marker}{notnull_marker}")
            schema_lines.extend(col_desc)
            
            # Foreign keys: id, seq, table, from, to
            cursor.execute(f"PRAGMA foreign_key_list('{table}');")
            fks = cursor.fetchall()
            if fks:
                fk_desc = ["  Foreign Keys:"]
                for fk in fks:
                    fk_desc.append(f"    * {fk[3]} -> {fk[2]}({fk[4]})")
                schema_lines.extend(fk_desc)
                
            # Sample rows (2 rows max for prompt context)
            cursor.execute(f"SELECT * FROM '{table}' LIMIT 2;")
            samples = cursor.fetchall()
            if samples:
                schema_lines.append("  Sample Rows:")
                for sample in samples:
                    schema_lines.append(f"    {dict(sample)}")
                    
        conn.close()
        return "\n".join(schema_lines)

    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validates SQL safety.
        Only SELECT statements are permitted to guarantee read-only analytical access.
        """
        cleaned_sql = sql_query.strip()
        
        # Strip trailing semicolon if present
        if cleaned_sql.endswith(";"):
            cleaned_sql = cleaned_sql[:-1].strip()
            
        # Check if starts with SELECT or WITH (for CTEs)
        if not re.match(r"^(SELECT|WITH)\b", cleaned_sql, re.IGNORECASE):
            return False, "Security Error: Only read-only SELECT or WITH queries are permitted."
            
        # Check for forbidden destructive keywords
        for kw_pattern in self.FORBIDDEN_KEYWORDS:
            if re.search(kw_pattern, cleaned_sql, re.IGNORECASE):
                matched = re.search(kw_pattern, cleaned_sql, re.IGNORECASE).group(0)
                return False, f"Security Violation: Destructive or unauthorized keyword '{matched}' detected."
                
        # Check for multi-statement execution attempts (e.g., SELECT ...; DROP ...)
        statements = [s.strip() for s in cleaned_sql.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Security Error: Multiple SQL statements in a single execution are prohibited."
            
        return True, None

    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Executes a validated SQL query against the SQLite database.
        Returns execution results, column metadata, row count, and latency.
        """
        is_valid, err = self.validate_sql(sql_query)
        if not is_valid:
            return {
                "success": False,
                "error": err,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": 0.0
            }
            
        start_time = time.perf_counter()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [dict(row) for row in cursor.fetchall()]
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            
            return {
                "success": True,
                "error": None,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_ms": round(elapsed_ms, 2)
            }
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "success": False,
                "error": f"Database execution error: {str(e)}",
                "columns": [],
                "rows": [],
                "row_count": 0,
                "execution_time_ms": round(elapsed_ms, 2)
            }
        finally:
            conn.close()

    @staticmethod
    def format_results_as_markdown(columns: List[str], rows: List[Dict[str, Any]]) -> str:
        """Formats tabular SQL query rows into a Markdown table."""
        if not rows or not columns:
            return "_No records returned._"
            
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        
        row_lines = []
        for r in rows:
            formatted_vals = []
            for col in columns:
                val = r.get(col, "")
                if isinstance(val, float):
                    formatted_vals.append(f"{val:,.2f}")
                else:
                    formatted_vals.append(str(val))
            row_lines.append("| " + " | ".join(formatted_vals) + " |")
            
        return "\n".join([header, separator] + row_lines)
