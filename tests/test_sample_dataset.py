"""Internal checks for sample answer keys and percentile-free paired selection."""
import csv
import itertools
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
import pandas as pd
from recon.__main__ import main
from recon.pipeline import ROOT


class FivePuzzleSample(unittest.TestCase):
    def test_all_five_gold_answers(self):
        with (ROOT / 'sample/puzzles.csv').open(encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
        self.assertEqual(reader.fieldnames, ['Puzzle_Number', 'Question_Number', 'Sample', 'Answer'])
        self.assertEqual(len(rows), 5)
        self.assertEqual([r['Answer'] for r in rows], list('DBEAC'))
        choices = lambda row: dict(re.findall(r'^\(([A-E])\) (.+)$', row['Sample'], re.M))
        orders = [p for p in itertools.permutations(['Amber','Birch','Cedar'])
                  if p.index('Amber') < p.index('Birch') and p.index('Cedar') == p.index('Amber') + 1]
        self.assertEqual(orders, [('Amber','Cedar','Birch')])
        self.assertEqual(choices(rows[0])['D'], ', '.join(orders[0]))
        people = ['Iris','Jade','Kai','Lena','Milo','Noor']
        groups = [set(c) for c in itertools.combinations(people, 3)]
        valid = [g for g in groups if 'Iris' in g and ('Iris' in g) != ('Jade' in g)
                 and ('Kai' in g) == ('Iris' in g) and ('Lena' in g) == ('Jade' in g)
                 and ('Milo' in g) != ('Noor' in g)]
        must = set.intersection(*valid)
        self.assertEqual([k for k,v in choices(rows[1]).items() if v in must], ['B'])
        allowed = lambda g: len(g)==3 and 'Aster' in g and ('Beryl' not in g or 'Coral' in g) and not {'Dune','Elm'} <= g
        self.assertEqual([k for k,v in choices(rows[2]).items() if allowed(set(v.split(', ')))], ['E'])
        parcel_orders = [p for p in itertools.permutations(['Red','Silver','Teal'])
                         if p[0]!='Red' and p[2]!='Silver' and p[2]=='Teal']
        self.assertEqual(parcel_orders, [('Silver','Red','Teal')])
        self.assertEqual(choices(rows[3])['A'], ', '.join(parcel_orders[0]))
        edges = {frozenset(e) for e in [('Alder','Brook'),('Brook','Cove'),('Brook','Dale')]}
        valid_choices=[]
        for k,v in choices(rows[4]).items():
            route=v.split(', ')
            if len(route)==3 and route[0]=='Alder' and route[-1]=='Dale' and all(frozenset(e) in edges for e in zip(route,route[1:])):
                valid_choices.append(k)
        self.assertEqual(valid_choices,['C'])

    def test_select_all_or_seeded_subset_without_percentiles(self):
        original = pd.read_csv(ROOT / 'sample/puzzles.csv')
        pool = original.assign(final_outcome='equivalent', final_adapted_puzzle=original.Sample)
        with tempfile.TemporaryDirectory(dir=ROOT / 'tests') as directory:
            work=Path(directory)
            source=work/'pool.jsonl'
            pool.to_json(source, orient='records', lines=True)
            def select(output, *extra):
                with patch.object(sys,'argv',['recon','select-pairs','--input',str(source),'--originals',str(ROOT/'sample/puzzles.csv'),'--output',str(output),*extra]):
                    main()
                return pd.read_csv(output)
            all_rows=select(work/'all.csv')
            self.assertEqual(len(all_rows),5)
            self.assertNotIn('Solved_Percentile',all_rows)
            first=select(work/'first.csv','--size','2','--seed','7')
            second=select(work/'second.csv','--size','2','--seed','7')
            self.assertEqual(list(first.adaptation_id),list(second.adaptation_id))
            with self.assertRaisesRegex(ValueError,'--size'):
                select(work/'too_many.csv','--size','6')


if __name__ == '__main__':
    unittest.main()
