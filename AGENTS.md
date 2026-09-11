# Shared AI Engineering Rules

These rules apply to Codex, Trae Work, Cursor, and any other engineering AI. Start every task by reading `PROJECT_CONTEXT.md`.

## Before Changing Anything

1. Check `git branch --show-current`, `git status --short`, and `git diff` / `git diff --cached`.
2. Read `PROJECT_CONTEXT.md` and the relevant existing code and tests.
3. Establish the baseline with `python -m pytest`.

Use the repository's real commands:

```bash
python -m pytest
python -m pytest tests/test_llm_contracts.py
python main.py
```

The targeted LLM-contract test is an offline smoke check: it stubs the LLM call. Do not make a real provider request when testing.

## Implementation Rules

- Make changes small, explicit, testable, and incremental.
- Reuse established logic and style; avoid needless comments, over-abstraction, and placeholder architecture.
- Preserve user changes. Never overwrite unrelated edits.
- Do not call real LLM APIs or use real API keys in tests. Do not delete a failing test merely to make the suite green.
- A strict xfail may be removed only after the underlying behavior is truly fixed and verified.
- Do not commit secrets.
- Do not substantially change `processor`, UI, or providers without approval.
- During V3.0, do not create `rag`, `agents`, `router`, `api`, or `vscode` modules and do not introduce tree-sitter, ANTLR, or JavaParser.

## Git Rules

- Do not force-push or rewrite history. Do not overwrite user work.
- Make each completed phase its own commit.
- Before handoff, report changed files, tests run, behavior changes, open problems, commit, and status.

## Roles

- Codex/GPT is the primary implementer.
- DeepSeek defaults to QA and documentation and must not overturn frozen architecture.
- Claude defaults to reviewer.
- If a tool does not automatically load these files, explicitly instruct it at task start to read `AGENTS.md` and `PROJECT_CONTEXT.md`.
