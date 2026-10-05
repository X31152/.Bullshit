# Agent Results

Shared report file. Every agent appends its findings here when done.

## How to report

1. `git fetch origin claude/shared-agent-results-3seueh && git checkout claude/shared-agent-results-3seueh && git pull origin claude/shared-agent-results-3seueh`
2. Append a new section at the **bottom** of this file using the template below. Do not edit other agents' sections.
3. Commit, then push: `git push -u origin claude/shared-agent-results-3seueh`
4. If the push is rejected, run `git pull --rebase origin claude/shared-agent-results-3seueh`. On a conflict in this file, keep **both** sides (yours and the others'), then `git rebase --continue` and push again.

## Template

```
## <Agent name / task> — <YYYY-MM-DD HH:MM UTC>

**Task:** what you were asked to do
**Status:** done / partial / blocked

### Findings
- ...

### Links / files / PRs
- ...

### Open questions / next steps
- ...
```

---

<!-- Agent reports go below this line -->
