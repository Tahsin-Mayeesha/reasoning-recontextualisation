"""Check publication files without printing detected secret values."""
import csv
import json
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parent.parent
SECRET = re.compile(r'sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{25,}')
FORBIDDEN = {'.csv', '.xlsx', '.xls', '.jsonl', '.pdf', '.zip', '.png', '.jpg'}
errors = []
for path in ROOT.rglob('*'):
    if not path.is_file() or any(p in {'.git', '.venv', '__pycache__', '.ipynb_checkpoints'} for p in path.parts):
        continue
    relative = path.relative_to(ROOT)
    # These root folders hold ignored local inputs and run outputs, not publication assets.
    if relative.parts[0] in {'data', 'outputs', 'private', 'build', 'dist'}:
        continue
    approved_sample = relative.as_posix() == 'sample/puzzles.csv'
    if approved_sample:
        with path.open(encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
        if reader.fieldnames != ['Puzzle_Number', 'Question_Number', 'Sample', 'Answer'] or len(rows) != 5:
            errors.append('Invalid five-puzzle sample schema or row count')
    if path.suffix.lower() in FORBIDDEN and not approved_sample:
        errors.append(f'Data/media artifact: {relative}')
    text = path.read_text(encoding='utf-8')
    if SECRET.search(text):
        errors.append(f'Credential-like value: {relative}')
    if path.name.startswith('.env') and path.name != '.env.example':
        errors.append(f'Environment file: {relative}')
    if path.suffix == '.ipynb':
        notebook = json.loads(text)
        for index, cell in enumerate(notebook['cells'], 1):
            if cell.get('outputs') or cell.get('attachments') or cell.get('execution_count') is not None:
                errors.append(f'Saved output/attachment/count: {relative}, cell {index}')
for error in errors:
    print(error)
print(f'Publication checks: {len(errors)} issues')
sys.exit(bool(errors))
