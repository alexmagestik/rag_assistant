"""
Document loader.
Currently supports .txt files; architecture is open for PDF / HTML extension.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple


def load_txt_files(data_dir: Path) -> Iterator[Tuple[str, str]]:
    """
    Yield (filename, text) for every .txt file in data_dir.
    Extensible: add loaders for PDF / HTML here.
    """
    for path in sorted(data_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        yield path.name, text
