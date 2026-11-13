"""Run with python -m recon --help from the repository root."""
import argparse
import json
from pathlib import Path
import pandas as pd
from .data import read_table, prepare, validate, stratify, KEYS
from .pipeline import run, write_json


def read_results(path):
    if Path(path).suffix == '.jsonl':
        return pd.read_json(path, lines=True, convert_dates=False)
    return read_table(path)


def export(frame, path):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Nested trace fields must remain valid JSON for audit notebooks.
    frame = frame.copy()
    for col in frame:
        frame[col] = frame[col].map(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
    frame.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(description='ReCon private-data experiment pipeline')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'sample', 'export', 'select-pairs', 'split-pairs', 'summarize'):
        p = sub.add_parser(name)
        p.add_argument('--input', required=True)
        p.add_argument('--output', required=True)
        if name in ('sample', 'select-pairs'):
            p.add_argument('--seed', required=True, type=int)
            p.add_argument('--counts', default='Hard:50,Medium:50,Easy:50' if name == 'sample' else 'Hard:34,Medium:34,Easy:32')
        if name == 'select-pairs':
            p.add_argument('--originals', required=True)
    for name in ('adapt', 'solve', 'audit-answer', 'audit-judge'):
        p = sub.add_parser(name)
        p.add_argument('--input', required=True)
        p.add_argument('--output', required=True, help='Private JSONL checkpoint')
        p.add_argument('--config', required=True)
        p.add_argument('--resume', action='store_true')
        p.add_argument('--limit', type=int)
        if name == 'solve':
            p.add_argument('--mode', choices=['zs', 'cot'], default='zs')
    args = parser.parse_args()
    frame = read_results(args.input)
    if args.command in ('adapt', 'solve', 'audit-answer', 'audit-judge'):
        if args.limit is not None:
            if args.limit < 1:
                parser.error('--limit must be positive')
            frame = frame.head(args.limit)
        config = json.loads(Path(args.config).read_text(encoding='utf-8'))
        if args.command == 'solve':
            mode = args.mode
            config['generator'] = {**config['generator'], **config.get('solve', {}).get(mode, {})}
        records = run(frame, config, args.output, stage=args.command, mode=getattr(args, 'mode', 'zs'), resume=args.resume)
        errors = sum(r.get('execution_status') == 'error' or r.get('final_outcome') in ('generation_failed', 'judge_failed') for r in records)
        print(f'{len(records)} rows checkpointed; {errors} execution/judge failures')
        if errors:
            raise SystemExit(2)
    elif args.command == 'prepare':
        export(prepare(frame), args.output)
    elif args.command == 'sample':
        validate(frame)
        counts = {k: int(v) for k, v in (part.split(':') for part in args.counts.split(','))}
        export(stratify(frame, counts, args.seed), args.output)
    elif args.command == 'export':
        export(frame, args.output)
    elif args.command == 'select-pairs':
        original = validate(read_table(args.originals))
        frame = frame[frame.final_outcome == 'equivalent'].copy()
        # Keep an adaptation ID: repeated source questions across generators are legitimate.
        frame['adaptation_id'] = [f'adaptation-{i:06d}' for i in range(len(frame))]
        if 'Solved_Percentile' not in frame:
            frame = frame.merge(original[KEYS + ['Solved_Percentile']], on=KEYS, how='left', validate='many_to_one')
        counts = {k: int(v) for k, v in (part.split(':') for part in args.counts.split(','))}
        selected = stratify(frame, counts, args.seed)
        selected = selected.drop(columns=['Sample', 'Answer'], errors='ignore')
        paired = selected.merge(original[KEYS + ['Sample', 'Answer']], on=KEYS, how='left', validate='many_to_one')
        if paired['Sample'].isna().any():
            raise ValueError('Missing original match')
        export(paired, args.output)
        # Use --input pairs.csv with the instructions in docs/REPRODUCIBILITY.md
    elif args.command == 'split-pairs':
        validate(frame)
        if not {'adaptation_id', 'final_adapted_puzzle'}.issubset(frame):
            raise ValueError('Use the output of select-pairs')
        original = frame.drop(columns=['final_adapted_puzzle'])
        adapted = original.copy()
        adapted['Sample'] = frame['final_adapted_puzzle']
        export(original, str(args.output) + '.original.csv')
        export(adapted, str(args.output) + '.adapted.csv')
    elif args.command == 'summarize':
        summary = {'rows': len(frame)}
        if 'final_outcome' in frame:
            summary['outcomes'] = frame.final_outcome.value_counts(dropna=False).to_dict()
        if {'Answer', 'Model_Answer'}.issubset(frame):
            gold = frame.Answer.astype(str).str.strip().str.upper()
            if not gold.isin(list('ABCDE')).all():
                raise ValueError('Gold Answer must be A-E for every row')
            prediction = frame.Model_Answer.fillna('').astype(str).str.strip().str.upper()
            summary.update(accuracy=float((gold == prediction).mean()), parsed=int(prediction.isin(list('ABCDE')).sum()))
        if Path(args.output).exists():
            raise FileExistsError(args.output)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, summary)


if __name__ == '__main__':
    main()
