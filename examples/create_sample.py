"""Create original synthetic sample inputs; no percentile metadata is required."""
import argparse
import csv
from pathlib import Path


def unit(context, clues, question, choices):
    return ('<context>\n' + context + '\n</context>\n<clues>\n' +
            '\n'.join(f'{i}. {clue}' for i, clue in enumerate(clues, 1)) +
            '\n</clues>\n<question>\n' + question + '\n' +
            '\n'.join(f'({letter}) {choice}' for letter, choice in zip('ABCDE', choices)) + '\n</question>')


def row(number, text, answer):
    return {'Puzzle_Number': f'SYN{number:03d}', 'Question_Number': 'Q1', 'Sample': text, 'Answer': answer}


ROWS = [
    row(1, unit(
        'Three delivery vans, Amber, Birch, and Cedar, occupy positions 1, 2, and 3 in a queue.\nEach van occupies exactly one position, and no position contains more than one van.',
        ['Amber is somewhere before Birch.', 'Cedar is immediately after Amber.'],
        'Which of the following must be the order of the vans, from position 1 to position 3?',
        ['Amber, Birch, Cedar', 'Birch, Amber, Cedar', 'Cedar, Amber, Birch', 'Amber, Cedar, Birch', 'Birch, Cedar, Amber']), 'D'),
    row(2, unit(
        'Six volunteers, Iris, Jade, Kai, Lena, Milo, and Noor, are assigned to teams 1 and 2.\nEach team has exactly three volunteers, and each volunteer belongs to exactly one team.',
        ['Iris and Jade are on different teams.', 'Kai is on the same team as Iris.',
         'Lena is on the same team as Jade.', 'Milo and Noor are on different teams.'],
        'If Iris is on team 1, which of the following must also be on team 1?',
        ['Jade', 'Kai', 'Lena', 'Milo', 'Noor']), 'B'),
    row(3, unit(
        'Exactly three sensors are selected from Aster, Beryl, Coral, Dune, and Elm.',
        ['Aster must be selected.', 'If Beryl is selected, Coral must also be selected.',
         'Dune and Elm cannot both be selected.'],
        'Which of the following could be the complete set of selected sensors?',
        ['Aster, Beryl, Dune', 'Beryl, Coral, Dune', 'Aster, Dune, Elm', 'Aster, Beryl, Elm', 'Aster, Beryl, Coral']), 'E'),
    row(4, unit(
        'Three parcels, Red, Silver, and Teal, occupy lockers 1, 2, and 3.\nEach locker contains exactly one parcel, and each parcel occupies exactly one locker.',
        ['Red is not in locker 1.', 'Silver is not in locker 3.', 'Teal is in locker 3.'],
        'Which of the following must list the parcels in lockers 1, 2, and 3, respectively?',
        ['Silver, Red, Teal', 'Red, Silver, Teal', 'Silver, Teal, Red', 'Teal, Red, Silver', 'Red, Teal, Silver']), 'A'),
    row(5, unit(
        'A rail network has four stations: Alder, Brook, Cove, and Dale.\nA direct link can be traveled in either direction. There are no links other than those listed.',
        ['Alder is directly linked to Brook.', 'Brook is directly linked to Cove.', 'Brook is directly linked to Dale.'],
        'Which of the following could be a route from Alder to Dale that uses exactly two direct links?',
        ['Alder, Cove, Dale', 'Alder, Dale', 'Alder, Brook, Dale', 'Alder, Brook, Cove, Dale', 'Alder, Cove, Brook, Dale']), 'C'),
]
ROW = ROWS[0]
SAMPLE = ROW['Sample']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='data/synthetic_puzzles.csv')
    parser.add_argument('--single', action='store_true', help='Write only the first puzzle')
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [ROW] if args.single else ROWS
    if output.suffix.lower() == '.csv':
        with output.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(ROW))
            writer.writeheader()
            writer.writerows(rows)
    elif output.suffix.lower() == '.xlsx':
        import pandas as pd
        pd.DataFrame(rows).to_excel(output, index=False)
    else:
        parser.error('--output must end in .csv or .xlsx')
    print(f'Created {output}: {len(rows)} original synthetic puzzles.')


if __name__ == '__main__':
    main()
