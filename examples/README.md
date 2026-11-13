# Five-puzzle Ollama example


The repository includes [sample/puzzles.csv](../sample/puzzles.csv), containing five original synthetic question units. No file-generation step is required.

| Puzzle | Constraint type | Gold answer |
|---|---|---|
| SYN001 | Ordering and adjacency | D |
| SYN002 | Grouping | B |
| SYN003 | Conditional selection | E |
| SYN004 | Assignment and fixed positions | A |
| SYN005 | Network routes | C |

### One complete input row

| Column | Value |
|---|---|
| `Puzzle_Number` | `SYN001` |
| `Question_Number` | `Q1` |
| `Sample` | The complete block below, in a single cell |
| `Answer` | `D` |

```xml
<context>
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
</question>
```

The unique valid order is Amber, Cedar, Birch. The gold answer is D. Gold labels are stored outside `Sample` and are not passed to models.

### Generate and judge adaptations with Ollama

After installing the package, start Ollama with `ollama serve` in a separate terminal if it is not already running. In your working terminal, download the example model and run all five rows:

```sh
ollama pull qwen3.5:9b
python -m recon adapt --generator-model qwen3.5:9b --judge-model qwen3.5:9b --think false --judge-think true --max-tokens 4000 --judge-max-tokens 8192 --num-ctx 16384 --judge-num-ctx 16384 --input sample/puzzles.csv --output outputs/sample_adaptations.jsonl
python -m recon export --input outputs/sample_adaptations.jsonl --output outputs/sample_adaptations.csv
```

This uses the same Qwen generator/judge combination as the existing experiment preset. For other installed chat-capable models, replace the two model tags independently. Omit the thinking flags unless you know the chosen models support them. These commands require a running Ollama server; successful adaptation depends on the actual model outputs.

### Solve the original sample

```sh
python -m recon solve --model qwen3.5:9b --input sample/puzzles.csv --mode zs --max-tokens 2048 --output outputs/sample_solve.jsonl
python -m recon summarize --input outputs/sample_solve.jsonl --output outputs/sample_solve_summary.json
```

The gold answers are D, B, E, A, and C. Summary accuracy compares the model's parsed predictions with these labels. Output files stay in ignored local folders. Use fresh output names for a new run, or `--resume` with unchanged inputs and settings.


To regenerate the five-puzzle CSV into a new local file, run `python examples/create_sample.py --output data/synthetic_puzzles.csv`. For an Excel copy, use `--output data/synthetic_puzzles.xlsx`. Run these commands from the repository root.
