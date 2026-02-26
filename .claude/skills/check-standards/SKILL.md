---
name: check-standards
description: Audit the project against CLAUDE.md dev standards. Checks package management, logging, polars usage, ruff linting, config patterns, and pipeline file structure.
allowed-tools: Bash
---

# Project Standards Audit

## Package management — no bare `pip install`, pyproject.toml present
!`grep -r "pip install" . --include="*.py" --include="*.sh" -l 2>/dev/null | grep -v ".venv" | grep -v ".git" || echo "CLEAN"`
!`ls pyproject.toml uv.lock 2>&1`

## Logging — no `logging.basicConfig`, all pipeline files use loguru
!`grep -rn "logging\.basicConfig\|import logging" pipeline/ 2>/dev/null || echo "CLEAN"`
!`grep -rn "from pipeline.config import logger\|from loguru" pipeline/ 2>/dev/null || echo "NONE FOUND"`

## Polars — no `.apply()`, check for pandas fallback
!`grep -rn "\.apply(" pipeline/ 2>/dev/null || echo "CLEAN"`
!`grep -rn "import pandas" pipeline/ 2>/dev/null || echo "CLEAN"`

## Hardcoded secrets — no API keys in source
!`grep -rn "ANTHROPIC_API_KEY\s*=\s*['\"]sk-\|REDDIT.*SECRET\s*=\s*['\"]" pipeline/ ui/ 2>/dev/null || echo "CLEAN"`

## Config pattern — require_env / optional_env usage
!`grep -rn "require_env\|optional_env" pipeline/ 2>/dev/null || echo "NONE FOUND"`
!`cat pipeline/config.py 2>/dev/null | head -40 || echo "config.py NOT FOUND"`

## Ruff lint
!`uv run ruff check . 2>&1 | tail -20`

## Ruff format check
!`uv run ruff format --check . 2>&1 | tail -10`

## Pipeline file structure
!`ls data/raw/ 2>/dev/null || echo "data/raw/ MISSING"`
!`ls data/processed/ 2>/dev/null || echo "data/processed/ MISSING"`
!`ls data/insights/ 2>/dev/null || echo "data/insights/ MISSING"`
!`ls pipeline/*.py 2>/dev/null || echo "pipeline/ MISSING"`

## CI config present
!`cat .github/workflows/ci.yml 2>/dev/null | head -30 || echo "ci.yml NOT FOUND"`

---

Analyse the evidence above and produce a concise adherence report:

1. **For each standard** (package mgmt, logging, polars, secrets, config, ruff, pipeline structure, CI): state ✅ PASS, ⚠️ WARN, or ❌ FAIL with a one-line reason.
2. **Summary line** at the top: overall status and count of failures/warnings.
3. **Action items** (if any): bullet list of concrete commands or file edits to fix failures.

Be brief — lead with the summary, then the per-standard table, then action items.
