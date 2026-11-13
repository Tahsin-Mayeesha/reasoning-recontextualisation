# Validation

Offline checks performed during consolidation:

- Sixteen unit/integration tests passed: answer extraction, judge schema validation, feedback refinement, parse exhaustion, missing-generation rejection, checkpoint resume identity, data preparation/stratification, paired selection/splitting, native Ollama request shape, canonical solver-prompt dispatch across all configured providers.
- Python source compilation passed for the reusable package, tests, and publication checker.
- CLI help loaded successfully.
- Publication checker: zero credential patterns, dataset/media artifacts, or saved notebook outputs/attachments/execution counts.
- SHA-256 verification: all 52 source code notebooks unchanged.
- The six canonical prompts were checked against rendered Appendix B.3.1–B.3.6. Active solver dispatch uses one shared prompt per mode across all providers.
- Every analysis copy's code matches its source modulo the documented credential redaction.

No API credentials were used, no paid requests were sent, no source data was submitted to providers, and no Ollama models were downloaded or run. SDK integrations and model availability still require a live check in the intended research environment. Offline tests do not verify paper scores or semantic equivalence.

The test suite uses artificial sentinel strings, not GRE examples. The GitHub Actions workflow installs the core dependencies and runs the tests and publication check without API secrets.

## Complete synthetic-input smoke check

The original example in `examples/create_sample.py` was checked independently by enumerating all six permutations. Only Amber, Cedar, Birch satisfies both constraints, so the gold option is D.

`tests/test_sample_workflow.py` creates the CSV and runs the actual CLI through original solving, scoring, adaptation with one rejected round and one repair, CSV export, paired-set selection/splitting, adapted CoT solving, scoring, and no-call resume. Provider HTTP responses are simulated while the real Ollama request construction and response parsing are exercised. Both simulated solver scores are 1/1; this is a fixture check, not a measured model result.

No provider API keys were configured in this session, and the local Ollama endpoint was unavailable. Live inference was therefore not validated. The publication checker excludes the designated ignored local `data/`, `outputs/`, and `private/` folders; it continues to check the publication source and assets.

## Model-independent Ollama selection

Five additional offline tests exercise arbitrary namespaced model tags, separate generator/judge endpoints, model-default and named thinking controls, an explicit solver configuration, native options, missing-judge validation, and resume rejection after a model change. They also check that replacing the Qwen preset does not inherit its forced thinking controls. These use simulated HTTP responses and do not certify live performance of arbitrary models.
