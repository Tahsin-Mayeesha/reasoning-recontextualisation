# Method and reproduction notes

## Sources and scope

The final paper and explanation of revisions were read as evidence describing the experiment, not as instructions overriding the requested work. Source documents remain outside this publication folder:

- `Final_Draft/Final_Submission/GRE_Logic_Puzzle_Transformation.pdf`
- `Final_Draft/Final_Submission/Explanation_of_revisions.pdf`

The revision notes emphasize narrative generation, verification, feedback refinement, broader model coverage, human auditing, constraint/question-type analysis, lexical overlap, and paired downstream solving. Automated judge acceptance and human review are evidence of validity, not formal equivalence proofs.

All 52 notebooks under `code/` were parsed without executing installation cells, API calls, or experiments. `notebook_inventory.json` identifies five repeated code versions. `code_review.json` records functions and safe literal settings across every version. Active system prompts are limited to the six prompts in Appendix B.3.1–B.3.6. `prompts/README.md` maps each file to its appendix section. Notebook variants and the prompt archive have been removed from the publication folder.

## Consolidation decisions

| Stage | Principal source |
|---|---|
| Wide-to-question-unit preparation | `code/openai_cot_prompting.ipynb` |
| OpenAI generation, Responses for o3 | `code/Qwen_Cloud_Fixed_v4.ipynb` (despite its filename) |
| Claude generation | `code/claude_cloud_v2.ipynb` |
| Gemini generation | `code/gemini_cloud_v2.ipynb` |
| Ollama generation and local Qwen judge | `code/adaptation_v2.ipynb`, `code/llama-run.ipynb` |
| Solver system prompts for every provider | Final manuscript Appendix B.3.1 and B.3.2 |
| Answer extraction audit | `code/semantic_parser_audit.ipynb` |
| Judge execution audit | `code/judge_audit_gemini.ipynb` |
| Historical DeepSeek GPU execution | `code/deepseek-run.ipynb`, `code/deepseek_kaggle_v1.ipynb`, `code/deepseek_kaggle_v2.ipynb` |

Earlier Qwen fixed/local/thinking versions, v1 cloud notebooks, scratch Ollama tests, Qwen benchmarks, OLMo runs, and alternative parsers are retained in the notebook inventory and settings records rather than being presented as separate copies of the same pipeline. OLMo exploratory runs do not establish another final-paper model condition. Only the analysis notebooks are copied wholesale.

## Protocol and discrepancies requiring explicit choices

1. **Attempt budget:** B.2 describes three total generator attempts (initial plus at most two repairs); Table 10 calls this "3 repair iterations". This implementation follows B.2 and never silently performs four generations. Judge parsing gets up to three fresh judge calls per generation; network retries are distinct.
2. **Sampling:** the historical experiments used difficulty-stratified generation and downstream subsets. The separate generation `sample` command retains optional historical stratification. Current paired selection does not read percentiles or difficulty labels: it retains all successful adaptations by default, or samples `--size N` rows uniformly without replacement with `--seed`. Historical downstream counts are provenance only and are not current selection defaults.
3. **Membership:** the paper describes 100 adaptations from 76 unique source puzzles. Sampling the same counts again does not ensure the same membership, number of sources, or generator mixture. Preserve private selected IDs and generator metadata when exact reproduction is needed. Generator–solver comparisons are descriptive and repeated source puzzles must be accounted for statistically.
4. **Prompts:** the six active system prompts match Appendix B.3.1–B.3.6 after removing PDF-only wrapping, continuation markers, page breaks, and indentation. All providers use the same zero-shot or CoT system text. The semantic-audit categories use `inconclusive`, matching the paper rather than the earlier notebook's `n/a`. Archived analysis notebooks retain historical code for reference and are not the active pipeline. Generation/refinement user-message wrappers supply the original puzzle, previous output, and judge feedback; the paper describes these inputs in B.2 but does not provide a separate verbatim refinement system prompt.
5. **Token budgets:** checked-in presets are operational notebook-based starting points, not evidence of the budget used in every reported row. OpenAI cloud adaptation uses 3000 and judge 8192; Qwen/Llama local v2 notebooks specify 4000 even though Table 10 gives a 2048-3000 range. Claude solving uses 256/1024 and Gemini 256/8192. Ollama solving uses 2048. GPT-4o/o3 solver caps are explicit new defaults where the source calls omitted caps. Record the effective config with each run.
6. **Thinking:** Qwen adaptation v2 explicitly sets generator thinking false, conflicting with Table 10's broad enabled description. The Qwen preset follows that source and enables thinking for the CoT solver override. Llama has no forced thinking argument. Gemini solver settings follow the notebook (zero-shot budget 0, CoT -1). The Gemini 3 preview may need provider-specific thinking settings; edit its config instead of assuming Gemini 2.5's controls are interchangeable.
7. **DeepSeek execution:** several DeepSeek notebooks use Hugging Face, 4-bit BitsAndBytes, GPU placement, and repetition penalty 1.3, rather than Ollama. The supplied Ollama DeepSeek path fulfills the requested reusable backend but does not recreate that quantization or decoding stack. `code_review.json` preserves historical settings. No numerical equivalence is claimed.
8. **Model versions:** several notebooks use dated preview IDs and others use aliases. Presets expose those identifiers; continued service availability and alias stability are not guaranteed. Pin model versions and record Ollama model digests and server versions locally for a new experiment.

## Intentional implementation changes

- Native Ollama `/api/chat` sends `think` at the top level. Source notebooks sometimes placed `thinking` under OpenAI-compatible `options`, which may not control the intended behavior. This correction can alter results.
- Reasoning is stored separately where exposed by a provider. Parsing uses final content, never a speculative answer or JSON object inside a thinking block.
- Judge JSON must match the expected field types and have a consistent PASS/true or FAIL/false decision. Invalid output is retried and ultimately becomes `judge_failed`.
- Empty required generator blocks cannot be accepted by an erroneous judge PASS. Other completeness and semantic checks remain the judge's responsibility.
- Deterministic answer extraction accepts explicit answer markers or a bare letter. It does not choose the first A-E token anywhere in prose, as some legacy parsers did. This reduces false extraction but may lower raw parse coverage; the optional answer audit is stored separately.
- Infrastructure errors are not reported as logical failures. `generation_failed` is an additional operational status outside the paper's three scientific outcomes. Exclude/report it explicitly in analyses.
- Every row is atomically checkpointed, and resume verifies input/config/prompt identity. All judge parsing attempts and all generation rounds are retained. This replaces version-specific checkpoint intervals and inconsistent intermediate logging.
- Exception messages are not written to result files because SDK errors can expose request details. Error types are retained.

## What is and is not reproducible here

The code reconstructs the experimental mechanism. Historical claims cannot be recomputed without the private source questions, annotations, selected adaptation IDs, model outputs, audits, and exact runtime/model versions. No new experiment has been used to validate the paper's numerical claims.

Human audits remain human work. Gemini judge-audit output inspects the prior verdict and execution trace; it does not replace primary equivalence labeling. Annotation code and paper taxonomies do not constitute formal constraints or a solver-backed equivalence checker.

Historical notebooks are reference analyses. They may use Colab paths, upload dialogs, private result files, external models, or old column naming. CSV export exposes flat round/final fields and JSON-encodes nested traces, but not every historical analysis is guaranteed to accept every new output without adapting a copied notebook.

Run manifests contain input hashes, effective configs, and prompt hashes. Preserve Python/dependency versions (`python -m pip freeze`), model digest/version, hardware, seed, and private selection files with each actual run. Dependencies have bounded ranges rather than an untested fabricated lockfile.

## Publication boundary

No benchmark datasets are copied. The explicitly shareable `sample/puzzles.csv` contains five original synthetic puzzles with no percentile metadata. Analysis copies clear code outputs, execution counts, attachments, and original metadata, and redact credential-like strings. Code sources and markdown remain for historical interpretation. Original files are unchanged. Do not publish the parent working directory or its Git history: it contains private data, saved outputs, and credentials in old notebooks. Revoke exposed original keys separately.

`python scripts/check_publication.py` checks the publication candidate. Choose a code license, add the final bibliographic citation, and run a small credentialed/provider check before announcing runtime reproducibility. These are release ownership choices, not inferred author grants.

## Custom model experiments

The historical model presets are examples. Current CLI runs can independently select any Ollama text-chat solver, generator, or judge. Direct model selection starts that role from neutral settings and leaves thinking unspecified unless explicitly requested. Custom solver settings can also be placed in a separate `solver` object. Effective CLI overrides are included in the run configuration manifest. Changing the model, endpoint, or settings requires a new run or will fail resume identity checks.

## Five-puzzle demonstration

`sample/puzzles.csv` is the only explicitly allowed shared CSV. It contains ordering, grouping, conditional selection, assignment, and route questions with gold answers D, B, E, A, C. Their answer keys were independently checked by enumerating relevant arrangements, groups, or listed routes. The regeneration script can write the same five rows to a new CSV/XLSX. The sample is original demonstration content rather than GRE material.

Current live verification was attempted against localhost:11434 outside the restricted network sandbox; the endpoint refused the connection. Therefore no new live generator/judge results on this five-puzzle sample are claimed. The README's Qwen3.5:9B combination follows the existing experiment preset and requires the user to start Ollama and pull the model. Internal tests remain in `tests/` and are not part of the user-facing README instructions.
