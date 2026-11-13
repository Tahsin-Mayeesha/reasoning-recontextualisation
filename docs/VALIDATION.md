# Validation

Offline checks performed during consolidation:

- Nine unit/integration tests passed: answer extraction, judge schema validation, feedback refinement, parse exhaustion, missing-generation rejection, checkpoint resume identity, data preparation/stratification, paired selection/splitting, native Ollama request shape.
- Python source compilation passed for the reusable package, tests, and publication checker.
- CLI help loaded successfully.
- Publication checker: zero credential patterns, dataset/media artifacts, or saved notebook outputs/attachments/execution counts.
- SHA-256 verification: all 52 source code notebooks unchanged.
- Every published archived prompt matches its recorded SHA-256.
- Every analysis copy's code matches its source modulo the documented credential redaction.

No API credentials were used, no paid requests were sent, no source data was submitted to providers, and no Ollama models were downloaded or run. SDK integrations and model availability still require a live check in the intended research environment. Offline tests do not verify paper scores or semantic equivalence.

The test suite uses artificial sentinel strings, not GRE examples. The GitHub Actions workflow installs the core dependencies and runs the tests and publication check without API secrets.
