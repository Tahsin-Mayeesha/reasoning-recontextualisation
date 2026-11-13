# Canonical prompts

The active pipeline uses exactly six system prompts. Their wording follows the official prompt blocks in Appendix B.3.1–B.3.6. PDF-only line wrapping, page breaks, continuation markers, and indentation are removed. Schema fields are presented as in the appendix, without adding surrounding JSON braces.

| File | Role | Appendix section | PDF pages |
|---|---|---|---|
| `zero_shot.txt` | Direct answer selection | B.3.1 | 17 |
| `cot.txt` | Stepwise solving with `<reasoning>` and `<answer>` output | B.3.2 | 17–18 |
| `generator.txt` | Narrative transformation and one-to-one entity mapping | B.3.3 | 18 |
| `judge.txt` | Structural and logical preservation verification | B.3.4 | 18–19 |
| `answer_audit.txt` | Extraction of the solver's committed answer | B.3.5 | 19 |
| `judge_audit.txt` | Audit of judge execution and verdict extraction | B.3.6 | 19–20 |

Source: `GRE_Logic_Puzzle_Transformation.pdf`, final submission. The source PDF is not bundled.

Every API and Ollama solver uses `zero_shot.txt` for `--mode zs` and `cot.txt` for `--mode cot`. Provider-specific reasoning controls and token budgets remain in `configs/`; they do not select a different system prompt.

The semantic-audit categories are `formatting_only`, `equivalence_issue`, `mixed`, and `inconclusive`, as printed in B.3.6. The earlier notebook category `n/a` is not used.

Generation and refinement use the same generator system prompt. User messages supply the source question and, during refinement, the previous output and judge feedback, following the procedure in B.2. The paper does not publish a separate verbatim refinement system prompt.

Historical prompt variants remain only within the preserved source/analysis notebooks. They are not selected by the reusable pipeline. The old active prompt archive, provider-specific duplicates, and notebook prompt manifest have been removed.

Changing prompts invalidates resume compatibility with prior runs. Start a new output file when switching from a notebook variant to this canonical prompt set.
