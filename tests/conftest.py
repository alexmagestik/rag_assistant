"""
conftest.py — автоматически добавляет корень проекта в sys.path.
Благодаря этому pytest находит модуль app при запуске из любой директории.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
