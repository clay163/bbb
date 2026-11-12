import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

app_file = ROOT / "frontend" / "app.py"
exec(compile(app_file.read_text(encoding="utf-8"), str(app_file), "exec"),
     {"__file__": str(app_file), "__name__": "__main__"})