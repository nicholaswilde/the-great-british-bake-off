# GitHub CLI (`gh`) Non-Interactive Execution

## Rule
Always pipe GitHub CLI (`gh`) commands to `cat` to bypass interactive prompts and terminal pagers:

```bash
rtk gh <command> | cat
```

## Guidelines
1. **Never Run Bare `gh` Interactively**: Without a pipe, `gh` may invoke a pager (e.g., `less`) or wait on interactive confirmation prompts, causing agent execution to hang.
2. **Combine with RTK**: Prefix with `rtk` to filter output tokens while piping to `cat` (e.g., `rtk gh issue list | cat`).
3. **Explicit Non-Interactive Flags**: Where applicable, provide required arguments explicitly (e.g., `--title`, `--body`, `--label`, `--non-interactive`) so `gh` does not prompt for missing fields.

## Examples
- `rtk gh issue list | cat`
- `rtk gh issue view 12 | cat`
- `rtk gh pr list | cat`
- `rtk gh pr diff 4 | cat`
- `rtk gh run list | cat`
