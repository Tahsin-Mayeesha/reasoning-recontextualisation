"""Write one original synthetic puzzle as CSV or XLSX for pipeline smoke checks."""
import argparse
import csv
from pathlib import Path

SAMPLE = '''<context>
Three delivery vans, Amber, Birch, and Cedar, occupy positions 1, 2, and 3 in a queue.
Each van occupies exactly one position, and no position contains more than one van.
</context>
<clues>
1. Amber is somewhere before Birch.
2. Cedar is immediately after Amber.
</clues>
<question>
Which of the following must be the order of the vans, from position 1 to position 3?
(A) Amber, Birch, Cedar
(B) Birch, Amber, Cedar
(C) Cedar, Amber, Birch
(D) Amber, Cedar, Birch
(E) Birch, Cedar, Amber
</question>'''

ROW = {'Puzzle_Number': 'SYN001', 'Question_Number': 'Q1', 'Sample': SAMPLE,
       'Answer': 'D', 'Solved_Percentile': 50}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='data/synthetic_puzzle.csv')
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == '.csv':
        with output.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(ROW))
            writer.writeheader()
            writer.writerow(ROW)
    elif output.suffix.lower() == '.xlsx':
        import pandas as pd
        pd.DataFrame([ROW]).to_excel(output, index=False)
    else:
        parser.error('--output must end in .csv or .xlsx')
    print(f'Created {output}; correct answer D. Percentile 50 is illustrative, not measured.')


if __name__ == '__main__':
    main()
