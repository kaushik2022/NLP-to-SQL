"""
cli.py
Interactive Command Line Interface for the NLP to SQL Query Assistant.
Demonstrates LangGraph-driven query translation, local SQLite execution, and response synthesis.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.sql_agent import NLToSQLAgent
from src.database import SQLiteDatabase
from src.config import settings

SAMPLE_QUESTIONS = [
    "Who are the top 5 highest paid employees and what are their departments?",
    "What is the total revenue and number of deals won in sales?",
    "Which sales representative generated the most revenue?",
    "List all company projects with their allocated budgets and current status.",
    "What is the average salary across each department?",
    "How many employees are in each department?",
    "What are the budgets and locations of all departments?"
]

def print_banner():
    banner = """
================================================================================
           NLP TO SQL QUERY ASSISTANT (LangChain + LangGraph + SQLite)          
================================================================================
Translates natural language questions into safe, optimized SQLite SQL queries.
Features schema mapping, security guardrails, low-latency execution, and synthesis.

Commands:
  /help       - Show sample natural language queries
  /schema     - Display live SQLite schema and sample records
  /samples    - Run an automated demo of predefined queries
  exit/quit   - Exit the application
================================================================================
"""
    print(banner)

def main():
    print_banner()

    try:
        agent = NLToSQLAgent()
    except FileNotFoundError:
        print("[!] Database not found. Automatically initializing SQLite database...")
        from seed_database import init_db
        init_db()
        agent = NLToSQLAgent()

    print(f"[i] Connected to local SQLite DB: {settings.db_path}")
    print("[i] Ready for natural language queries.\n")

    while True:
        try:
            user_input = input("NLP-SQL> ").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                print("\nGoodbye!")
                break

            if user_input.lower() == "/help":
                print("\nTry asking questions like:")
                for idx, sample in enumerate(SAMPLE_QUESTIONS, 1):
                    print(f"  {idx}. {sample}")
                print()
                continue

            if user_input.lower() == "/schema":
                print("\n" + agent.db.get_schema_info() + "\n")
                continue

            if user_input.lower() == "/samples":
                print("\n--- Running Automated Demonstration of Sample Questions ---\n")
                for q in SAMPLE_QUESTIONS[:3]:
                    print(f"\n[Query]: {q}")
                    result = agent.run(q)
                    print(result["response"])
                    print("-" * 60)
                continue

            # Process query through LangGraph
            print("\n[Thinking] Analyzing request & querying SQLite database...\n")
            result = agent.run(user_input)
            print(result["response"])
            print("\n" + "=" * 80 + "\n")

        except KeyboardInterrupt:
            print("\nSession interrupted. Exiting.")
            break
        except Exception as e:
            print(f"\n[Error]: {e}\n")

if __name__ == "__main__":
    main()
