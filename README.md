# Reasoning Recontextualisation

Tools for transforming logic puzzles into new narrative settings while preserving their constraints, questions, and answer correspondence. Use the pipelines to compare language models as puzzle solvers, generators, and judges.

The workflow supports API models from OpenAI, Anthropic, and Google, plus local models served through Ollama. Generator and judge settings are configured independently. Each run records intermediate outputs, feedback, and final decisions for later analysis.

## Workflow

![Generation, verification, and optional refinement, illustrated by an actor-selection puzzle transformed into a garden-selection puzzle.](assets/recontextualisation_workflow.svg)

The example preserves a one-to-one entity mapping, all three constraints, and the correct answer's option position. It passed verification on the first attempt; the dashed feedback branch shows how rejected generations are refined. The figure uses shortened wording for readability.

1. Prepare structured multiple-choice question units.
2. Evaluate solvers on the original questions.
3. Generate adaptations with explicit entity mappings.
4. Judge structural and logical preservation, then refine rejected adaptations.
5. Evaluate solvers on matched original and adapted questions.
6. Audit output parsing and analyze results.

A judge's acceptance is a model-based assessment of equivalence. It does not constitute a formal proof.

## Install

Use Python 3.10+ and run commands from this repository's root:

```sh
python -m venv .venv
# Activate .venv using your shell's standard activation command.
python -m pip install -e ".[api,analysis]"
python -m recon --help
```

For Ollama-only runs, install the core package with `python -m pip install -e .`. Start Ollama separately and download the models you plan to use:

```sh
ollama serve
# In another terminal:
ollama pull qwen3.5:9b
ollama pull llama3.1:8b
```

Model tags in the configuration files are editable presets. Check that the selected model is installed or available from its provider. Different model versions, quantization settings, and serving engines can change results.

Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GEMINI_API_KEY` in your process environment for the provider you select. `.env.example` lists the variable names. `.env` is not loaded automatically.

## Input format

Supply your own CSV or XLSX files with one row per question. A five-puzzle synthetic demonstration is included in `sample/puzzles.csv`. Supply your own data for larger experiments; benchmark datasets and generated puzzle collections are not bundled.

| Column | Meaning |
|---|---|
| `Puzzle_Number` | Source puzzle identifier |
| `Question_Number` | Question identifier, consistent across stages |
| `Sample` | Full `<context>`, `<clues>`, and `<question>` unit, including A-E choices |
| `Answer` | Gold letter A-E, needed for scoring and paired-set construction |

Keys must be unique within a run. Paired sets also carry `adaptation_id` to distinguish adaptations of the same source question by different generators. Only the puzzle text in `Sample` is sent to the solver or generator; gold labels remain available for evaluation.

To convert a wide-format workbook containing `Puzzle_Number`, `Context`, `Clues`, `Q1`, `Q2`, and subsequent question columns:

```sh
python -m recon prepare --input private/puzzles.xlsx --output data/questions.csv
```

Attach gold labels by puzzle/question keys after preparation. The converter does not assume an answer-column layout or perform OCR.

## Try the five-puzzle sample

The repository includes [sample/puzzles.csv](sample/puzzles.csv), containing five original synthetic question units. No file-generation step is required.

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

## API models

API generators use provider-specific SDKs. The supplied adaptation presets use a local Qwen judge, which requires a running Ollama server even when the generator is an API model.

```sh
python -m recon solve --config configs/api/openai_gpt4o.json --input data/questions.csv --mode zs --output outputs/gpt4o_original_zs.jsonl
python -m recon adapt --config configs/api/openai_o3.json --input data/questions.csv --output outputs/o3_adaptations.jsonl
python -m recon adapt --config configs/api/claude_haiku.json --input data/questions.csv --output outputs/claude_adaptations.jsonl
python -m recon adapt --config configs/api/gemini_25_flash.json --input data/questions.csv --output outputs/gemini_adaptations.jsonl
```

Use `--mode cot` for explicit stepwise solver prompting. The o3 preset uses native reasoning with medium effort. Additional configuration files include Gemini 3 Flash Preview generation. Provider availability and supported reasoning controls vary by model.

## Local models with Ollama

Use any chat-capable model tag available on your Ollama server. Model selection is independent for solving, adaptation generation, and judging. The Qwen, Llama, and DeepSeek configuration files remain sample presets; none is a required model.

### Choose models directly

No configuration file is needed. Replace the quoted model tags below with exact tags from `ollama list`:

```sh
python -m recon solve --model "YOUR_SOLVER:TAG" --input data/synthetic_puzzle.csv --mode zs --output outputs/custom_solve.jsonl
python -m recon adapt --generator-model "YOUR_GENERATOR:TAG" --judge-model "YOUR_JUDGE:TAG" --input data/synthetic_puzzle.csv --output outputs/custom_adapt.jsonl
```

Use the same tag in both adaptation roles for a self-judge experiment, or different tags for an independent judge. Config-free adaptation requires an explicit judge model. The six canonical prompts stay unchanged across models.

### Servers and generation controls

Both roles default to `http://localhost:11434`. Override their server roots independently:

```sh
python -m recon adapt --generator-model "YOUR_GENERATOR:TAG" --base-url http://localhost:11434 --judge-model "YOUR_JUDGE:TAG" --judge-base-url http://localhost:11435 --max-tokens 4000 --judge-max-tokens 8192 --num-ctx 16384 --judge-num-ctx 16384 --input data/synthetic_puzzle.csv --output outputs/custom_servers.jsonl
```

Primary-role options are `--think`, `--max-tokens`, `--num-ctx`, `--temperature`, and `--timeout`. Adaptation also accepts their independent `--judge-...` equivalents. The same `--model` and primary controls are available for `audit-answer` and `audit-judge`.

Thinking is omitted by default for direct model selection, allowing the model's own behavior. Use `--think auto` to clear a preset's thinking setting, `--think true` or `--think false` for compatible models, or the exact named level supported by that model. Use `--judge-think` separately for the judge. Do not assume every model supports the same thinking controls. See [Ollama's thinking documentation](https://docs.ollama.com/capabilities/thinking) for discovering supported values with `/api/show`.

### Keep reusable configurations

Copy [configs/ollama/custom.example.json](configs/ollama/custom.example.json), replace its model tags, and pass it with `--config`. The optional `solver` role selects a solver independently of the adaptation `generator`; existing presets reuse `generator` for solving. Each role can set its own `base_url`, `max_tokens`, `num_ctx`, `temperature`, `think`, and `timeout`. For additional native generation settings, supply an `options` object such as `{"seed": 42, "top_p": 0.9}`. An optional `keep_alive` setting is also forwarded to Ollama. Top-level token/context/temperature controls take precedence over their corresponding `options` entries.

Existing example presets work as before:

```sh
python -m recon adapt --config configs/ollama/qwen.json --input data/questions.csv --output outputs/qwen_adaptations.jsonl
python -m recon adapt --config configs/ollama/llama.json --input data/questions.csv --output outputs/llama_adaptations.jsonl
python -m recon solve --config configs/ollama/llama.json --input data/questions.csv --mode cot --output outputs/llama_original_cot.jsonl
```

You can override a preset's judge while retaining its generator:

```sh
python -m recon adapt --config configs/api/openai_o3.json --judge-model "YOUR_JUDGE:TAG" --input data/questions.csv --output outputs/o3_custom_judge.jsonl
```

Selecting a new model with `--model`, `--generator-model`, or `--judge-model` replaces that role's preset, avoiding inherited thinking controls from another model. Apply any desired role settings explicitly afterward. Overrides are recorded in the run manifest, so resume refuses a changed model or effective configuration.

The selected model must support text chat, fit in the available hardware, and produce the required answer or judge format. Model-independent transport does not guarantee reasoning accuracy or reliable judging for every model. The DeepSeek Ollama sample uses a different execution stack from the archived Hugging Face / BitsAndBytes runs.

## Paired evaluation

Paired evaluation requires only the source IDs, source question text, gold answers, and successful adaptations. It does not use `Solved_Percentile`, difficulty labels, or stratification.

Select all successful adaptations and construct matching original/adapted solver inputs:

```sh
python -m recon select-pairs --input outputs/sample_adaptations.jsonl --originals sample/puzzles.csv --output outputs/sample_pairs.csv
python -m recon split-pairs --input outputs/sample_pairs.csv --output outputs/sample_pairs
python -m recon solve --model qwen3.5:9b --input outputs/sample_pairs.original.csv --mode zs --output outputs/paired_original_solve.jsonl
python -m recon solve --model qwen3.5:9b --input outputs/sample_pairs.adapted.csv --mode zs --output outputs/paired_adapted_solve.jsonl
```

Only judge-accepted adaptations enter the paired set, so it can contain fewer than five rows. If none is accepted, selection reports an error. For a larger private adaptation pool, add `--size 100 --seed 42` to select 100 successful adaptation rows uniformly without replacement. Omit `--size` to retain all successful rows.

Selection does not balance generators or enforce one adaptation per source puzzle. Join paired results using `adaptation_id` and source IDs. Account for repeated source puzzles when performing statistical comparisons. Historical difficulty-stratified generation sampling remains available through the separate `sample` command; it is not used for paired evaluation.

## Checkpoints and results

Each completed row is atomically checkpointed to JSONL. Adaptation records retain generation rounds, raw responses, available reasoning, entity mappings, judge parsing attempts, feedback, and final outcomes. A run manifest records input content hashes, effective configuration, prompt hashes, stage, and solver mode.

Repeat a command with `--resume` to skip checkpointed rows. Resume requires identical inputs, configuration, prompts, and stage. Failed rows remain checkpointed; retry them in a separate run. Use `--limit 2` for a small live check. Runs containing infrastructure or judge failures exit with status 2 after saving results.

Export results, inspect judge execution, audit answer extraction, or summarize accuracy:

```sh
python -m recon export --input outputs/o3_adaptations.jsonl --output outputs/o3_adaptations.csv
python -m recon audit-judge --config configs/api/gemini_audit.json --input outputs/o3_adaptations.jsonl --output outputs/o3_judge_audit.jsonl
python -m recon audit-answer --config configs/api/gemini_audit.json --input outputs/gpt4o_original_zs.jsonl --output outputs/gpt4o_answer_audit.jsonl
python -m recon summarize --input outputs/gpt4o_original_zs.jsonl --output outputs/gpt4o_summary.json
```

Audits append separate fields and preserve primary decisions. Missing predictions count as incorrect when scoring. Judge audits inspect prior verdicts and execution traces; they do not independently establish puzzle equivalence.

## Repository layout

- `recon/`: data preparation, provider transports, parsers, experiment stages, and CLI.
- `configs/api/` and `configs/ollama/`: editable model and runtime presets.
- `prompts/`: six canonical solver, generator, judge, and audit prompts. All providers share the same solver prompts; see [the prompt guide](prompts/README.md).
- `analysis/notebooks/`: archived analysis notebooks with saved outputs cleared and credentials redacted.
- `docs/notebook_inventory.json` and `docs/code_review.json`: source notebook inventory, duplicate relationships, and configuration records.
- `docs/REPRODUCIBILITY.md`: implementation provenance, configuration differences, and reproduction limits.
- `scripts/check_publication.py`: checks for credentials, dataset artifacts, and saved notebook outputs.

See [the analysis guide](analysis/README.md) before using the archived notebooks. They retain their original file-path and column assumptions and may need local configuration.

## Data handling

API stages send the selected puzzle content to the configured provider and can incur charges. Keep source benchmark data, generated adaptations, traces, result files, and credentials in ignored local folders. The only shared input data is the original synthetic five-puzzle sample. Review files and Git history before sharing a repository. Select a code license before distributing the project.
