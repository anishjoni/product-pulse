---
name: check-ci
description: Check GitHub Actions CI status after a push or PR merge. Fetches the latest workflow runs, surfaces any failures with step-level detail, and suggests fixes. Use after `git push` or when CI might have errors.
allowed-tools: Bash
---

# CI Status Check

## Repository context
- **Branch:** !`git branch --show-current`
- **Latest local commit:** !`git log --oneline -1`

## Recent workflow runs
!`gh run list --limit 8 2>&1`

## Failed job details (most recent failure)
!`
RUN_ID=$(gh run list --limit 8 --json databaseId,conclusion 2>/dev/null \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)
failed = [r for r in runs if r.get('conclusion') == 'failure']
print(failed[0]['databaseId'] if failed else '')
")

if [ -z "$RUN_ID" ]; then
  echo "No failed runs in the last 8 — all green or still running."
else
  gh run view "$RUN_ID" 2>&1
fi
`

---

Analyse the CI results above and do the following:

1. **State clearly** whether CI is passing or failing.
2. **If failing:** identify the exact step(s) that failed and explain the most likely cause based on what you know about this project (ruff lint, ruff format, pytest, uv sync issues, etc.).
3. **Suggest a concrete fix** — include the exact command(s) to run locally to reproduce and resolve the issue.
4. **If passing:** confirm all green and note any warnings worth watching.

Keep the response concise — lead with the status, then the fix.
