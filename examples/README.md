# Complete synthetic input example

This original example can be shared. It contains no benchmark question or model-generated dataset. Run commands from the repository root.

```sh
python examples/create_sample.py --output data/synthetic_puzzle.csv
```

The script uses a CSV writer to quote the multiline `Sample` correctly. To create an Excel equivalent, use `--output data/synthetic_puzzle.xlsx`.

## One complete input row

| Column | Value |
|---|---|
| `Puzzle_Number` | `SYN001` |
| `Question_Number` | `Q1` |
| `Sample` | The complete block below, in a single cell |
| `Answer` | `D` |
| `Solved_Percentile` | `50`, illustrative metadata only; not a measured human score |

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

The unique valid order is Amber, Cedar, Birch. The gold answer is D. Gold labels and percentile metadata are stored outside `Sample` and are not passed to models.

## Live checks

These commands require Ollama to be running with `qwen3.5:9b` downloaded:

```sh
python -m recon solve --config configs/ollama/qwen.json --input data/synthetic_puzzle.csv --mode zs --output outputs/sample_solve.jsonl
python -m recon summarize --input outputs/sample_solve.jsonl --output outputs/sample_solve_summary.json
python -m recon adapt --config configs/ollama/qwen.json --input data/synthetic_puzzle.csv --output outputs/sample_adapt.jsonl
python -m recon export --input outputs/sample_adapt.jsonl --output outputs/sample_adapt.csv
```

A successful solver should output D. Adaptation acceptance depends on what the live generator and judge produce. To use a cloud generator, replace the config with an API preset and set that provider's API key. The configured judge still requires Ollama.

Run the offline end-to-end check without a model server or API credentials:

```sh
python -m unittest discover -s tests -p test_sample_workflow.py -v
```

That test invokes the real CLI, data loader, official prompts, Ollama request builder, parsers, checkpointing, feedback refinement, paired-set construction, both solver modes, scoring, and CSV export. HTTP responses are simulated. It verifies plumbing and deterministic behavior, not model accuracy or a real judge's equivalence assessment.

Output files stay in ignored local folders. Use fresh output names for a new run, or `--resume` with unchanged inputs/configuration.
