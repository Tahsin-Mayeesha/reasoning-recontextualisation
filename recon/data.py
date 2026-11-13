"""Private data loading and reproducible preparation."""
from pathlib import Path
import pandas as pd

KEYS = ['Puzzle_Number', 'Question_Number']


def read_table(path):
    path = Path(path)
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path, keep_default_na=False)
    if path.suffix.lower() == '.xlsx':
        return pd.read_excel(path, keep_default_na=False)
    raise ValueError('Input must be CSV or XLSX')


def validate(frame, sample=True, unique=True):
    required = KEYS + (['Sample'] if sample else [])
    missing = set(required) - set(frame.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if frame[required].astype(str).apply(lambda s: s.str.strip().eq('')).any().any():
        raise ValueError('Required fields cannot be blank')
    if unique and frame.duplicated(KEYS + (['adaptation_id'] if 'adaptation_id' in frame else [])).any():
        raise ValueError('Duplicate puzzle/question keys; separate generator variants into separate runs')
    return frame


def prepare(frame):
    columns = sorted([c for c in frame if __import__('re').fullmatch(r'Q\d+', str(c))], key=lambda c: int(c[1:]))
    if not columns or not {'Puzzle_Number', 'Context', 'Clues'}.issubset(frame.columns):
        raise ValueError('Wide input requires Puzzle_Number, Context, Clues, Q1...Qn')
    records = []
    for _, row in frame.iterrows():
        for col in columns:
            question = str(row[col]).strip()
            if not question:
                continue
            sample = ('Your task is to provide the correct answer to the given puzzle using the clues.\n'
                      f"<context> {row['Context']} </context>\n<clues> {row['Clues']} </clues>\n<question> {question} </question>")
            record = {'Puzzle_Number': row['Puzzle_Number'], 'Question_Number': col, 'Sample': sample}
            for extra in ['Solved_Percentile', 'difficulty']:
                if extra in frame:
                    record[extra] = row[extra]
            # No assumed answer-column convention: attach gold labels explicitly by key.
            records.append(record)
    return validate(pd.DataFrame(records))


def difficulty(frame):
    frame = frame.copy()
    if 'Solved_Percentile' not in frame:
        raise ValueError('Solved_Percentile (0-100) is required for stratification')
    p = pd.to_numeric(frame['Solved_Percentile'], errors='raise')
    if not p.between(0, 100).all():
        raise ValueError('Solved_Percentile must be between 0 and 100')
    frame['difficulty'] = p.map(lambda x: 'Hard' if x < 30 else 'Medium' if x < 60 else 'Easy')
    return frame


def stratify(frame, counts, seed):
    frame = difficulty(frame)
    return pd.concat([frame[frame.difficulty == group].sample(n=count, random_state=seed)
                      for group, count in counts.items()], ignore_index=True)
