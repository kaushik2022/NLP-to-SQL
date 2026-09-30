"""
src/config.py
Configuration settings for the NLP to SQL Query Assistant.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
# Load .env file automatically
load_dotenv(BASE_DIR / ".env")

DEFAULT_DB_PATH = BASE_DIR / "data" / "company_database.sqlite"

@dataclass
class Settings:
    db_path: Path = Path(os.getenv("SQL_DB_PATH", str(DEFAULT_DB_PATH)))
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    model_name: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    temperature: float = 0.0
    max_tokens: int = 1000
    safe_mode: bool = True  # Enforce SELECT-only queries

settings = Settings()
