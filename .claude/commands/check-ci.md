---
description: Check GitHub Actions CI status after a push or PR merge. Fetches the latest workflow runs, surfaces any failures with step-level detail, and suggests fixes.
allowed-tools: Bash
---

# CI Status Check

## Repository context
- **Repo:** !`git remote get-url origin 2>/dev/null | sed 's/.*github.com\///; s/\.git$//'`
- **Branch:** !`git branch --show-current`
- **Latest local commit:** !`git log --oneline -1`

## Recent workflow runs
!`
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com\///; s/\.git$//')
AUTH=""
[ -n "$GITHUB_TOKEN" ] && AUTH="-H \"Authorization: token $GITHUB_TOKEN\""

curl -s $AUTH \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/actions/runs?per_page=8" \
| python3 -c "
import sys, json
data = json.load(sys.stdin)
runs = data.get('workflow_runs', [])
if not runs:
    print('No runs found. If this is a private repo, set GITHUB_TOKEN in your shell.')
    sys.exit()
icons = {'success': '✅', 'failure': '❌', 'cancelled': '⚠️', 'skipped': '⏭️', 'timed_out': '⏱️'}
for r in runs:
    conclusion = r.get('conclusion') or 'running'
    icon = icons.get(conclusion, '🔄')
    print(f\"{icon}  {conclusion:<12}  {r['name']:<20}  {r['head_branch']:<20}  {r['created_at'][:16]}  {r['html_url']}\")
"
`

## Failed job details (most recent failure)
!`
REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com\///; s/\.git$//')
AUTH=""
[ -n "$GITHUB_TOKEN" ] && AUTH="-H \"Authorization: token $GITHUB_TOKEN\""

RUN_ID=$(curl -s $AUTH \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/actions/runs?per_page=8" \
| python3 -c "
import sys, json
runs = json.load(sys.stdin).get('workflow_runs', [])
failed = [r for r in runs if r.get('conclusion') == 'failure']
print(failed[0]['id'] if failed else '')
")

if [ -z "$RUN_ID" ]; then
  echo "No failed runs in the last 8 — all green or still running."
else
  curl -s $AUTH \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/jobs" \
  | python3 -c "
import sys, json
jobs = json.load(sys.stdin).get('jobs', [])
for job in jobs:
    status = job.get('conclusion', 'running')
    icon = '✅' if status == 'success' else ('❌' if status == 'failure' else '🔄')
    print(f\"\n{icon} Job: {job['name']}  ({status})\")
    for step in job.get('steps', []):
        if step.get('conclusion') == 'failure':
            print(f\"   └─ FAILED step: {step['name']}\")
"
fi
`

---

Analyse the CI results above:

1. **State clearly** whether CI is passing or failing.
2. **If failing:** identify the exact step(s) that failed and explain the most likely cause (ruff lint, ruff format, pytest, uv sync, etc.).
3. **Suggest the exact fix** — commands to run locally to reproduce and resolve.
4. **If passing:** confirm all green and note anything worth watching.
