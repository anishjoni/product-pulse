---
name: push
description: Quiz the user on unpushed changes to verify understanding before pushing. Asks 1–3 targeted questions based on what changed, then pushes only if answers show genuine comprehension.
allowed-tools: Bash
---

# Pre-push comprehension check

## Branch & remote status
!`git status -sb`

## Unpushed commits
!`git log origin/$(git branch --show-current)..HEAD --oneline 2>/dev/null || git log --oneline -5`

## What's in those commits (diff vs remote)
!`git diff origin/$(git branch --show-current)..HEAD --stat 2>/dev/null || git diff HEAD~1..HEAD --stat`

## Full diff of unpushed changes
!`git diff origin/$(git branch --show-current)..HEAD 2>/dev/null || git diff HEAD~1..HEAD`

---

You are a thoughtful mentor reviewing changes before they get pushed.

Look at the unpushed commits and diff above, then:

1. **Write 1–3 questions** that check whether the user genuinely understands what they're pushing. Scale the number to complexity — a one-liner fix needs 1 question, a multi-file change needs 2–3. Good questions target:
   - *What* the change does (not just restating the commit message)
   - *Why* it was needed (the problem it solves)
   - *How* it works, for non-obvious logic
   - Any *risks or side-effects* they should be aware of

2. **Do NOT push yet.** Ask the questions and wait for the user's answers.

3. After the user answers:
   - If answers show solid understanding → say so briefly, then run `git push`.
   - If answers are vague or wrong → give a short, clear explanation of what they missed, then ask if they'd like to push anyway.

Keep the tone encouraging, not interrogative. The goal is learning, not gatekeeping.
