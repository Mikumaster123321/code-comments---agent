# V3.0.0

## Release Summary

Project-level Maintenance Core Foundation

## Highlights

- Engineering baseline
- Stable `SymbolId`
- Project Scanner
- Project Graph
- Project Snapshot
- Deterministic Analysis Engine
- BYOK Provider Foundation
- Task-scoped Provider Isolation

## Existing Capabilities Preserved

- Python / Java documentation generation
- Translation
- Markdown API docs
- Diff
- Batch processing
- Gradio UI
- Multi-provider access

## BYOK

Users provide their own Provider, Model, and Credential. V3.0.0 does not include a
developer-owned third-party API key.

## Quality

- Tests: **129 passed**
- RC1.4 Full-System QA: **PASS**
- Claude Final Review: **APPROVE WITH NON-BLOCKING NOTES**
- Release Blockers: **0**

## Known Non-Blocking Limitations

- Selected legacy module comments still reference V2
- Legacy future-task Provider UI configuration remains process-level
- Selected maintenance debt remains deferred

## Roadmap

- V3.0.1 Managed AI Access & Credits — Planned
- V3.1 RAG — Planned
- V3.2 Multi-Agent — Planned
- V3.3 Router — Planned
- V3.4 VS Code — Planned
