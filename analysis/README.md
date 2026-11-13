# Historical analysis notebooks

`notebooks/` contains 28 distinct copies from `Results_notebooks/`, the top level of `Final_Draft/`, and analysis/audit notebooks under `code/`. Exact code duplicates are collapsed; every considered source maps to its copy in `manifest.json`.

Original code and markdown are retained in these copies except that credential-like values are redacted. Outputs, execution counts, attachments, and original metadata are removed to exclude saved puzzle text, traces, plots, and account details. Source originals have not been edited.

The collection covers solver accuracy, original/adapted comparisons, constraint/question-type associations, generator–solver analysis, visualizations, Jaccard overlap, error taxonomies, answer/judge audits, and additional revision probes. Exploratory probes are not all part of the central ReCon pipeline.

Install the analysis extra, then run `jupyter lab`. Update the input/path configuration cells in your local copy to use private data. Some notebooks use Colab upload helpers or install their own dependencies and some analyses call paid models. Review the relevant setup cells before execution; these notebooks have not been executed during consolidation.

To use reusable pipeline results with a notebook, first export JSONL to CSV using `python -m recon export`. Flat round fields and final outcomes are included; full traces remain in JSON-encoded columns. Historical column names and per-model file lists may require explicit mapping. Preserve the primary `Model_Answer` and audited answer separately when comparing parsing protocols.

Paired solver results include `adaptation_id`. Join on it as well as the source question IDs, retain generator identity, and account for repeated source puzzles in inferential analyses. No result tables or notebook figures are distributed as part of this folder.
