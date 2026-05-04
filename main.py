"""
Entry point for the RAG Assistant CLI.

Usage:
    python main.py
"""
from dotenv import load_dotenv

load_dotenv()

from app.cli.interface import run_cli

if __name__ == "__main__":
    run_cli()
