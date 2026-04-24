import os
from pathlib import Path

TEMP_DIR = Path("temp_reports")
files = list(TEMP_DIR.glob("*.md"))

print(f"Verifying {len(files)} files...")
for f in files:
    content = f.read_text(encoding='utf-8')
    words = content.split()
    print(f"{f.name}: {len(words)} words")
