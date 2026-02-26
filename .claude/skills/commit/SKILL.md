---
name: commit
description: Stage changed tracked files and commit with a short, readable summary of the changes. Skips untracked files unless they're clearly part of the current work.
allowed-tools: Bash
---

# Commit changes

## Current branch
!`git branch --show-current`

## Staged + unstaged changes
!`git status --short`

## What changed (diff summary)
!`git diff HEAD --stat`

## Full diff (for message generation)
!`git diff HEAD`

---

Look at the diff above and do the following:

1. **Identify** which files changed and what the changes accomplish in plain terms.
2. **Stage** only the modified/deleted tracked files (`git add -u`). Do NOT stage untracked files (shown as `??`) unless they are clearly part of the current change (e.g. a new file that was just created as part of this task).
3. **Write a commit message** that is:
   - One short subject line (≤72 chars, imperative mood: "Fix", "Add", "Update", not "Fixed"/"Added")
   - No body unless the change genuinely needs explanation
   - Honest — describe what changed, not why the task was assigned
4. **Commit** using the message, appending the co-author line:
   ```
   Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
   ```
5. **Confirm** with the commit hash and subject line.

Do NOT push. Do NOT amend previous commits.
