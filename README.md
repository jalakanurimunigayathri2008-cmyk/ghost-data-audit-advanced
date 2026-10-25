# Ghost Data Still Exists — Advanced Deletion Audit Agent

A modular Python baseline for the HackerRank Orchestrate challenge. It reads deletion requests,
identity history, deletion rules, and evidence files; resolves aliases; proposes evidence-linked
findings and ordered remediation; and writes `output.csv`.

**Important:** this is a runnable engineering baseline, not a claim of canonical accuracy. The
official `dataset/` is not included. Merge this source into the official repository, preserve its
dataset, inspect `AGENTS.md`, then calibrate the evidence and rule mappings against sample outputs.

## Design highlights
- Deterministic, auditable Python pipeline; no API key or paid model required.
- Identity alias graph from current and historical records.
- CSV, JSON, JSONL, TXT, LOG and SQL text readers; optional PDF/image extraction.
- Policy-based delete/redact/anonymize/retain handling.
- Active sync/import/index/export and backup/restore risk detection.
- Deterministic operation/phase ordering and output validation.
- Evaluation and token-usage templates with no fabricated metrics.

## Run from official repository root
Python 3.10+ recommended.

```powershell
python code/main.py --dataset dataset --output output.csv
python -m unittest discover -s tests -v
```

Optional PDF/image support: `pip install -r requirements-optional.txt`.

The program expects `dataset/deletion_requests.csv`. It looks for identity, audit, rules, manifest,
and `dataset/evidence/` files by their challenge-provided names. Verify the actual schema before
submission. A missing evidence match is treated as incomplete, not proof of deletion.

## Deliverables
The challenge asks for `output.csv` (518 sorted rows), `code.zip`, a development transcript, and an
AI interview. `code.zip` must include `evaluation/evaluation_report.md` and
`evaluation/usage_report.md`. Fill evaluation reports only with measured results from a real run.

## Privacy
Use only challenge synthetic data. Never commit API keys, `.env`, or personal customer data.
The system proposes actions; it does not connect to or modify real production systems.
